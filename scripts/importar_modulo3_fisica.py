#!/usr/bin/env python3
"""Importa o Módulo 3 sem apagar o banco nem alterar os Módulos 1 e 2."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from curriculo.physics_module3_source import validate_source, validate_zip_archive


def import_module(data: dict) -> dict:
    """Inicializa Django e grava somente os registros identificados como Módulo 3."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()

    from django.db import transaction
    from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao

    @transaction.atomic
    def save():
        summary = validate_source(data)
        materia, _ = Materia.objects.update_or_create(slug='fisica', defaults={
            'nome': 'Física', 'descricao': 'Mecânica, termologia, ondas, circuitos e Física Moderna',
            'icone': 'atom', 'ordem': 1, 'ativo': True,
        })
        disciplina, _ = Disciplina.objects.update_or_create(slug='fisica', defaults={
            'nome': 'Física', 'descricao': 'Trilha de Física', 'materia': materia,
            'icone': 'atom', 'ordem': 1, 'ativo': True, 'autor': None,
        })
        modulo, _ = Modulo.objects.update_or_create(disciplina=disciplina, ordem=3, defaults={
            'titulo': 'Módulo 3', 'descricao': data.get('title', 'Circuitos, campos e Física Moderna'),
        })

        phases = {phase['number']: phase for phase in data['phases']}
        phase_objects = {}
        for number, phase in phases.items():
            obj, _ = Fase.objects.update_or_create(
                modulo=modulo, ordem=number,
                defaults={'titulo': phase['title'], 'tipo': 'quiz', 'xp_recompensa': 0, 'moedas_recompensa': 0},
            )
            phase_objects[number] = obj

        expected_ids = []
        for exercise in data['exercises']:
            expected_ids.append(exercise['id'])
            answer = exercise['challenge']['answer']
            kind = answer['type']
            dynamic = {
                **exercise,
                'source_schema_version': data.get('schema_version'),
                'source_constants': data.get('constants', {}),
                'source_module': 3,
                'source_phase_id': phases[exercise['phase']]['id'],
                'source_phase_metadata': phases[exercise['phase']],
                'source_exercise_id': exercise['id'],
            }
            question, _ = Questao.objects.update_or_create(
                fase=phase_objects[exercise['phase']], codigo_fonte=exercise['id'],
                defaults={
                    'enunciado': exercise['challenge']['prompt'],
                    'explicacao_erro': answer.get('explanation', answer.get('solution', '')),
                    'tipo_resposta': kind, 'codigo_fonte': exercise['id'],
                    'dados_dinamicos': dynamic,
                },
            )
            question.opcoes.all().delete()
            if kind == 'choice':
                choices = answer.get('choices', answer.get('options', []))
                Opcao.objects.bulk_create([
                    Opcao(questao=question, texto=label, e_correta=(index == answer['correct']), ordem=index + 1)
                    for index, label in enumerate(choices)
                ])

        return {
            **summary, 'materia_id': materia.pk, 'disciplina_id': disciplina.pk,
            'modulo_id': modulo.pk,
            'phase_ids': {str(number): phase.pk for number, phase in phase_objects.items()},
            'exercise_ids': sorted(expected_ids),
        }

    return save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', default=str(PROJECT_ROOT / 'modulo3_fisica.json'),
                        help='Caminho para o JSON oficial do Módulo 3.')
    parser.add_argument('--zip', default=str(PROJECT_ROOT / 'exercicios.zip'),
                        help='ZIP com os exercícios individuais para comparação.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valida JSON e ZIP sem inicializar Django ou modificar o banco.')
    args = parser.parse_args()

    data = json.loads(Path(args.json).read_text(encoding='utf-8'))
    summary = validate_source(data)
    zip_path = Path(args.zip)
    if zip_path.is_file():
        summary['zip_validation'] = validate_zip_archive(zip_path, data['exercises'])
    if args.dry_run:
        print(json.dumps({'status': 'dry_run_ok', **summary}, ensure_ascii=False, indent=2))
        return
    result = import_module(data)
    print(json.dumps({'status': 'success', **result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
