"""Validação pura da fonte oficial do Módulo 3 de Física."""
from __future__ import annotations

import math
from curriculo.physics_engine import FORMULAS, calculate, validate_scene_parameters
from curriculo.physics_scenes import validate_scene

PHASE_COUNTS = {1: 12, 2: 12, 3: 6}
EXPECTED_TYPES = {'choice': 12, 'numeric': 18}
EXPECTED_MODULE = 3


def validate_source(data: dict) -> dict:
    if data.get('module') != EXPECTED_MODULE:
        raise ValueError('a fonte não identifica o Módulo 3')
    phases, exercises = data.get('phases'), data.get('exercises')
    if not isinstance(phases, list) or len(phases) != 3:
        raise ValueError('Módulo 3 deve conter exatamente três fases')
    if not isinstance(exercises, list) or len(exercises) != 30:
        raise ValueError('Módulo 3 deve conter exatamente 30 exercícios')

    phase_by_number = {p.get('number'): p for p in phases}
    if set(phase_by_number) != set(PHASE_COUNTS):
        raise ValueError('numeração de fases inválida')
    phase_ids = [p.get('id') for p in phases]
    if any(not value for value in phase_ids) or len(set(phase_ids)) != 3:
        raise ValueError('IDs de fases ausentes ou duplicados')

    ids = [e.get('id') for e in exercises]
    if any(not value for value in ids) or len(set(ids)) != 30:
        raise ValueError('IDs de exercícios ausentes ou duplicados')

    counts = {number: 0 for number in PHASE_COUNTS}
    types = {'choice': 0, 'numeric': 0}
    scenes, formulas = set(), set()
    for exercise in exercises:
        exercise_id = exercise['id']
        phase_number = exercise.get('phase')
        if phase_number not in PHASE_COUNTS:
            raise ValueError(f'fase inválida em {exercise_id}')
        counts[phase_number] += 1
        for key in ('title', 'context', 'learning_objective'):
            if not isinstance(exercise.get(key), str) or not exercise[key].strip():
                raise ValueError(f'{key} ausente em {exercise_id}')

        simulation = exercise.get('simulation') or {}
        scene = simulation.get('scene')
        validate_scene(scene)
        scenes.add(scene)
        params = simulation.get('parameters')
        if not isinstance(params, list):
            raise ValueError(f'parâmetros ausentes em {exercise_id}')
        values, keys = {}, set()
        for item in params:
            required = {'key', 'label', 'value', 'unit', 'min', 'max', 'step'}
            if not isinstance(item, dict) or not required.issubset(item):
                raise ValueError(f'parâmetro incompleto em {exercise_id}')
            key = item['key']
            numeric = [item[name] for name in ('value', 'min', 'max', 'step')]
            if not isinstance(key, str) or not key or key in keys:
                raise ValueError(f'chave de parâmetro ausente/duplicada em {exercise_id}')
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in numeric):
                raise ValueError(f'valor numérico inválido em {exercise_id}: {key}')
            if item['step'] <= 0 or item['min'] > item['max'] or not item['min'] <= item['value'] <= item['max']:
                raise ValueError(f'intervalo inválido em {exercise_id}: {key}')
            keys.add(key)
            values[key] = item['value']
        validate_scene_parameters(scene, values)

        answer = exercise.get('challenge', {}).get('answer', {})
        kind = answer.get('type')
        if kind not in types:
            raise ValueError(f'tipo de resposta inválido em {exercise_id}')
        types[kind] += 1
        if kind == 'choice':
            choices = answer.get('choices', answer.get('options'))
            correct = answer.get('correct')
            if not isinstance(choices, list) or len(choices) not in (3, 4) or not all(isinstance(x, str) and x.strip() for x in choices):
                raise ValueError(f'alternativas inválidas em {exercise_id}')
            if not isinstance(correct, int) or correct not in range(len(choices)):
                raise ValueError(f'gabarito inválido em {exercise_id}')
            if not answer.get('explanation'):
                raise ValueError(f'explicação ausente em {exercise_id}')
        else:
            formula = answer.get('formula')
            tolerance = answer.get('tolerance')
            if formula not in FORMULAS:
                raise ValueError(f'fórmula não suportada em {exercise_id}: {formula}')
            if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
                raise ValueError(f'tolerância inválida em {exercise_id}')
            if not isinstance(answer.get('digits'), int) or not answer.get('unit') or not answer.get('display_unit'):
                raise ValueError(f'unidade/precisão inválida em {exercise_id}')
            calculate(formula, values, data.get('constants'))
            formulas.add(formula)

    if counts != PHASE_COUNTS:
        raise ValueError(f'distribuição por fase inválida: {counts}')
    if types != EXPECTED_TYPES:
        raise ValueError(f'distribuição por tipo inválida: {types}')
    if len(scenes) != 29 or len(formulas) != 18:
        raise ValueError(f'catálogo incompleto: {len(scenes)} cenas / {len(formulas)} fórmulas')

    for phase in phases:
        actual = {e['id'] for e in exercises if e['phase'] == phase['number']}
        listed = phase.get('exercise_ids', [])
        if set(listed) != actual or len(listed) != len(actual):
            raise ValueError(f'lista de exercícios inconsistente na fase {phase["number"]}')

    return {
        'module': 3, 'phases': 3, 'exercises': 30, 'types': types,
        'scenes_count': len(scenes), 'scenes': sorted(scenes),
        'formulas_count': len(formulas), 'formulas': sorted(formulas),
    }


def validate_zip_archive(zip_path, exercises):
    import json
    import zipfile

    expected = {item['id']: item for item in exercises}
    found = {}
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.endswith('/') or not name.lower().endswith('.json'):
                continue
            item = json.loads(archive.read(name).decode('utf-8'))
            exercise_id = item.get('id')
            if not exercise_id or exercise_id in found:
                raise ValueError(f'ID ausente ou duplicado no ZIP: {name}')
            found[exercise_id] = item
    missing = set(expected) - set(found)
    extra = set(found) - set(expected)
    divergent = {key for key in set(expected) & set(found) if expected[key] != found[key]}
    if missing or extra or divergent:
        raise ValueError(
            f'ZIP divergente: faltantes={len(missing)}, extras={len(extra)}, '
            f'divergências={len(divergent)}'
        )
    return {'zip_files': len(found), 'missing': 0, 'extra': 0, 'divergences': 0}
