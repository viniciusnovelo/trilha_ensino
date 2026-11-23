"""Validação pura das fontes de conteúdo; não acessa banco nem importa Django."""
from curriculo.physics_engine import FORMULAS, calculate
from curriculo.physics_scenes import validate_scene
import math

EXPECTED_PHASES = {'Cinemática': 6, 'Dinâmica': 6, 'Trabalho, Energia e Potência': 8, 'Gravitação Universal': 8}

def validate_source(data: dict) -> dict:
    phases, exercises = data.get('phases'), data.get('exercises')
    if not isinstance(phases, list) or len(phases) != 4:
        raise ValueError('fonte deve conter exatamente 4 fases')
    if not isinstance(exercises, list) or len(exercises) != 28:
        raise ValueError('fonte deve conter exatamente 28 exercícios')
    ids = [e.get('id') for e in exercises]
    phase_ids = [p.get('id') for p in phases]
    if len(set(phase_ids)) != 4 or any(not x for x in phase_ids):
        raise ValueError('IDs de fases ausentes ou duplicados')
    if len(set(ids)) != 28 or any(not x for x in ids):
        raise ValueError('IDs de exercícios ausentes ou duplicados')
    by_phase = {p['number']: p for p in phases}
    if len(by_phase) != 4:
        raise ValueError('números de fase ausentes ou duplicados')
    counts = {p['title']: 0 for p in phases}
    kinds = {'numeric': 0, 'choice': 0}
    formulas, scenes = set(), set()
    for exercise in exercises:
        phase = exercise.get('phase')
        if phase not in by_phase:
            raise ValueError(f"fase inexistente no exercício {exercise['id']}: {phase}")
        if not isinstance(exercise.get('title'), str) or not exercise['title'] or not exercise.get('challenge', {}).get('prompt'):
            raise ValueError(f"título ou enunciado ausente em {exercise['id']}")
        completion = exercise.get('completion', {})
        if not isinstance(completion.get('xp'), int) or completion['xp'] < 0 or not completion.get('mastery_tag'):
            raise ValueError(f"dados de conclusão inválidos em {exercise['id']}")
        counts[by_phase[phase]['title']] += 1
        answer = exercise.get('challenge', {}).get('answer', {})
        kind = answer.get('type')
        if kind not in kinds:
            raise ValueError(f"tipo de resposta inválido em {exercise['id']}: {kind}")
        kinds[kind] += 1
        sim = exercise.get('simulation') or {}
        scene = sim.get('scene')
        validate_scene(scene)
        scenes.add(scene)
        params = sim.get('parameters')
        if not isinstance(params, list):
            raise ValueError(f"parâmetros ausentes em {exercise['id']}")
        if not isinstance(sim.get('show_vectors'), bool) or not isinstance(sim.get('show_live_readouts'), bool):
            raise ValueError(f"flags da simulação inválidas em {exercise['id']}")
        keys = set()
        parameter_values = {}
        for item in params:
            required = {'key', 'label', 'value', 'unit', 'min', 'max', 'step', 'hint'}
            if not required.issubset(item):
                raise ValueError(f"parâmetro incompleto em {exercise['id']}")
            if not isinstance(item['key'], str) or not item['key'] or not isinstance(item['label'], str):
                raise ValueError(f"identificação do parâmetro inválida em {exercise['id']}")
            numeric_values = [item['value'], item['min'], item['max'], item['step']]
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in numeric_values):
                raise ValueError(f"valores numéricos inválidos em {exercise['id']}: {item['key']}")
            if item['key'] in keys or item['step'] <= 0 or item['min'] > item['max'] or not item['min'] <= item['value'] <= item['max']:
                raise ValueError(f"parâmetro inválido em {exercise['id']}: {item['key']}")
            keys.add(item['key']); parameter_values[item['key']] = item['value']
        if kind == 'numeric':
            formula = answer.get('formula')
            if formula not in FORMULAS:
                raise ValueError(f"fórmula não suportada: {formula}")
            if not isinstance(answer.get('tolerance'), (int, float)) or not math.isfinite(answer['tolerance']) or answer['tolerance'] < 0:
                raise ValueError(f"tolerância inválida em {exercise['id']}")
            if not isinstance(answer.get('digits'), int) or answer['digits'] < 0 or not answer.get('unit') or not answer.get('display_unit'):
                raise ValueError(f"precisão inválida em {exercise['id']}")
            # Calcula com os valores-padrão: também detecta parâmetros incompatíveis.
            calculate(formula, parameter_values, data.get('constants'))
            formulas.add(formula)
        else:
            opts = answer.get('options')
            correct = answer.get('correct')
            if not isinstance(opts, list) or len(opts) != 3 or not all(isinstance(x, str) and x for x in opts):
                raise ValueError(f"choice deve possuir exatamente 3 alternativas: {exercise['id']}")
            if not isinstance(correct, int) or correct not in range(3):
                raise ValueError(f"índice da alternativa correta inválido: {exercise['id']}")
            if not answer.get('explanation'):
                raise ValueError(f"explicação ausente: {exercise['id']}")
    for phase in phases:
        listed = phase.get('exercise_ids', [])
        actual = [e['id'] for e in exercises if e['phase'] == phase['number']]
        if set(listed) != set(actual) or len(listed) != len(actual):
            raise ValueError(f"exercise_ids não correspondem à fase {phase['number']}")
    if counts != EXPECTED_PHASES:
        raise ValueError(f"distribuição por fase inválida: {counts}")
    if kinds != {'numeric': 21, 'choice': 7}:
        raise ValueError(f"distribuição por tipo inválida: {kinds}")
    if len(scenes) != 26 or len(formulas) != 21:
        raise ValueError(f"cenas/fórmulas distintas inválidas: {len(scenes)}/{len(formulas)}")
    return {'phases': len(phases), 'exercises': len(exercises), 'types': kinds, 'scenes': sorted(scenes), 'formulas': sorted(formulas)}



def validate_zip_archive(zip_path, exercises):
    import json
    import zipfile
    expected = {item['id']: item for item in exercises}
    found = {}
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if name.endswith('/') or not name.lower().endswith('.json'):
                continue
            payload = json.loads(archive.read(name).decode('utf-8'))
            exercise_id = payload.get('id')
            if not exercise_id:
                raise ValueError(f'JSON sem id dentro do ZIP: {name}')
            if exercise_id in found:
                raise ValueError(f'ID duplicado no ZIP: {exercise_id}')
            found[exercise_id] = payload
    missing = sorted(set(expected) - set(found))
    extra = sorted(set(found) - set(expected))
    divergent = sorted(key for key in set(expected) & set(found) if expected[key] != found[key])
    if missing or extra or divergent:
        raise ValueError('JSON principal e ZIP não correspondem. '
                         f'faltantes={len(missing)}, extras={len(extra)}, divergências={len(divergent)}')
    return {'zip_files': len(found), 'missing': 0, 'extra': 0, 'divergences': 0}