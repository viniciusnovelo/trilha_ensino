"""Validação da fonte oficial do Módulo 2 de Física."""
from __future__ import annotations
import math
from curriculo.physics_engine import FORMULAS, calculate, validate_scene_parameters
from curriculo.physics_scenes import validate_scene

PHASE_COUNTS = {1: 8, 2: 8, 3: 10, 4: 8}
EXPECTED_MODULE = 2


def validate_source(data: dict) -> dict:
    phases, exercises = data.get('phases'), data.get('exercises')
    if data.get('module') != EXPECTED_MODULE:
        raise ValueError('a fonte não identifica o Módulo 2')
    if not isinstance(phases, list) or len(phases) != 4:
        raise ValueError('Módulo 2 deve conter quatro fases')
    if not isinstance(exercises, list) or len(exercises) != 34:
        raise ValueError('Módulo 2 deve conter 34 exercícios')
    phase_by_number = {p.get('number'): p for p in phases}
    if set(phase_by_number) != set(PHASE_COUNTS):
        raise ValueError('numeração de fases inválida')
    ids = [e.get('id') for e in exercises]
    if len(set(ids)) != 34 or any(not x for x in ids):
        raise ValueError('IDs de exercícios ausentes ou duplicados')
    counts = {n: 0 for n in PHASE_COUNTS}
    types = {'choice': 0, 'numeric': 0}
    scenes, formulas = set(), set()
    for e in exercises:
        phase = e.get('phase')
        if phase not in PHASE_COUNTS:
            raise ValueError(f"fase inválida em {e.get('id')}")
        counts[phase] += 1
        if not e.get('title') or not e.get('context') or not e.get('learning_objective'):
            raise ValueError(f"conteúdo pedagógico incompleto: {e['id']}")
        sim = e.get('simulation') or {}
        scene = sim.get('scene')
        validate_scene(scene)
        scenes.add(scene)
        params = sim.get('parameters')
        if not isinstance(params, list):
            raise ValueError(f"parâmetros ausentes: {e['id']}")
        values, keys = {}, set()
        for p in params:
            required = {'key','label','value','unit','min','max','step'}
            if not required.issubset(p):
                raise ValueError(f"parâmetro incompleto: {e['id']}")
            vals = [p[k] for k in ('value','min','max','step')]
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals):
                raise ValueError(f"valor não numérico: {e['id']} / {p['key']}")
            if p['key'] in keys or p['step'] <= 0 or p['min'] > p['max'] or not p['min'] <= p['value'] <= p['max']:
                raise ValueError(f"intervalo inválido: {e['id']} / {p['key']}")
            keys.add(p['key']); values[p['key']] = p['value']
        validate_scene_parameters(scene, values)
        answer = e.get('challenge',{}).get('answer',{})
        kind = answer.get('type')
        if kind not in types:
            raise ValueError(f"tipo de resposta inválido: {e['id']}")
        types[kind] += 1
        if kind == 'choice':
            choices, correct = answer.get('choices'), answer.get('correct')
            if not isinstance(choices,list) or len(choices) != 4 or not all(isinstance(x,str) and x for x in choices):
                raise ValueError(f"questão de escolha deve conter quatro alternativas: {e['id']}")
            if not isinstance(correct,int) or correct not in range(4) or not answer.get('explanation'):
                raise ValueError(f"gabarito/explicação inválidos: {e['id']}")
        else:
            formula = answer.get('formula')
            if formula not in FORMULAS or not isinstance(answer.get('tolerance'),(int,float)) or answer['tolerance'] < 0:
                raise ValueError(f"fórmula ou tolerância inválida: {e['id']}")
            if not isinstance(answer.get('digits'),int) or not answer.get('unit') or not answer.get('display_unit'):
                raise ValueError(f"unidade/precisão inválida: {e['id']}")
            calculate(formula, values, data.get('constants'))
            formulas.add(formula)
    if counts != PHASE_COUNTS:
        raise ValueError(f"distribuição de exercícios inválida: {counts}")
    if len(scenes) != 34 or len(formulas) != 17:
        raise ValueError(f"catálogo incompleto: {len(scenes)} cenas / {len(formulas)} fórmulas")
    for p in phases:
        actual = {e['id'] for e in exercises if e['phase'] == p['number']}
        if set(p.get('exercise_ids',[])) != actual or len(p.get('exercise_ids',[])) != len(actual):
            raise ValueError(f"lista de exercícios inconsistente na fase {p['number']}")
    return {'phases':4,'exercises':34,'types':types,'scenes':sorted(scenes),'formulas':sorted(formulas)}


def validate_zip_archive(zip_path, exercises):
    import json, zipfile
    expected = {e['id']:e for e in exercises}
    found = {}
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith('.json') or name.endswith('/'):
                continue
            item = json.loads(archive.read(name).decode('utf-8'))
            key = item.get('id')
            if not key or key in found:
                raise ValueError(f'ID ausente ou duplicado no ZIP: {name}')
            found[key] = item
    missing = set(expected)-set(found); extra = set(found)-set(expected)
    divergent = {k for k in set(expected)&set(found) if expected[k] != found[k]}
    if missing or extra or divergent:
        raise ValueError(f'ZIP divergente: faltantes={len(missing)}, extras={len(extra)}, divergências={len(divergent)}')
    return {'zip_files':len(found),'missing':0,'extra':0,'divergences':0}
