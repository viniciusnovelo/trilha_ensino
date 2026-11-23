#!/usr/bin/env python3
"""Importa os dados-fonte oficiais do Módulo 1 de Física para os models Django."""
from __future__ import annotations
import json
from pathlib import Path
from django.db import transaction
from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from curriculo.physics_source import validate_source


@transaction.atomic
def import_module(data: dict) -> dict:
    summary = validate_source(data)
    materia, _ = Materia.objects.update_or_create(slug='fisica', defaults={
        'nome': 'Física', 'descricao': data.get('title', ''), 'icone': 'atom', 'ordem': 1, 'ativo': True,
    })
    disciplina, _ = Disciplina.objects.update_or_create(slug='fisica', defaults={
        'nome': 'Física', 'descricao': data.get('title', ''), 'materia': materia,
        'icone': 'atom', 'ordem': 1, 'ativo': True, 'autor': None,
    })
    modulo, _ = Modulo.objects.update_or_create(disciplina=disciplina, ordem=1, defaults={
        'titulo': data.get('module', 'Módulo 1'), 'descricao': data.get('title', ''),
    })
    phase_objects = {}
    for phase in data['phases']:
        obj, _ = Fase.objects.update_or_create(modulo=modulo, ordem=phase['number'], defaults={
            'titulo': phase['title'], 'tipo': 'quiz', 'xp_recompensa': 0, 'moedas_recompensa': 0,
        })
        phase_objects[phase['number']] = obj
    expected_ids = set()
    for exercise in data['exercises']:
        expected_ids.add(exercise['id'])
        answer = exercise['challenge']['answer']
        kind = answer['type']
        dynamic = {
            **exercise,
            'source_schema_version': data.get('schema_version'),
            'source_constants': data.get('constants', {}),
            'source_module': data.get('module'),
            'source_phase_id': next(p['id'] for p in data['phases'] if p['number'] == exercise['phase']),
            'source_phase_metadata': next(p for p in data['phases'] if p['number'] == exercise['phase']),
        }
        question, _ = Questao.objects.update_or_create(
            fase=phase_objects[exercise['phase']],
            codigo_fonte=exercise['id'],
            defaults={
                'enunciado': exercise['challenge']['prompt'],
                'explicacao_erro': answer.get('explanation', exercise['challenge'].get('solution', '')),
                'tipo_resposta': kind,
                'codigo_fonte': exercise['id'],
                'dados_dinamicos': {**dynamic, 'source_exercise_id': exercise['id']},
            },
        )
        question.opcoes.all().delete()
        if kind == 'choice':
            Opcao.objects.bulk_create([
                Opcao(questao=question, texto=text, e_correta=(index == answer['correct']), ordem=index + 1)
                for index, text in enumerate(answer['options'])
            ])
    return {**summary, 'materia_id': materia.pk, 'disciplina_id': disciplina.pk, 'modulo_id': modulo.pk,
            'phase_ids': {str(k): v.pk for k, v in phase_objects.items()}, 'exercise_ids': sorted(expected_ids)}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))