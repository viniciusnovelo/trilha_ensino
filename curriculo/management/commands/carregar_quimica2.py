import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao


class Command(BaseCommand):
    help = 'Importa os módulos e exercícios da Química 2 a partir do JSON fornecido.'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', default='modulo2_quimica.json')

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options['arquivo'])
        if not path.exists():
            raise CommandError(f'Arquivo não encontrado: {path}')
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f'Não foi possível ler o JSON: {exc}')

        quimica1 = Disciplina.objects.filter(slug='quimica-1').first()
        materia = (quimica1.materia if quimica1 else None) or Materia.objects.filter(slug__icontains='quim').first()
        if materia is None:
            materia = Materia.objects.create(nome='Química', slug='quimica', ordem=2, ativo=True)
        disciplina, _ = Disciplina.objects.get_or_create(
            slug='quimica-2',
            defaults={
                'nome': data.get('module', {}).get('title', 'Química 2'),
                'descricao': data.get('module', {}).get('description', ''),
                'materia': materia,
                'autor': quimica1.autor if quimica1 else None,
                'tema': quimica1.tema if quimica1 else 'tema-padrao',
                'ordem': 2,
                'ativo': quimica1.ativo if quimica1 else False,
            },
        )
        disciplina.nome = data.get('module', {}).get('title', 'Química 2')
        disciplina.descricao = data.get('module', {}).get('description', '')
        disciplina.materia = materia
        if quimica1:
            disciplina.autor = quimica1.autor
            disciplina.tema = quimica1.tema
            disciplina.ativo = quimica1.ativo
        disciplina.save()

        existing_modules = {m.ordem: m for m in disciplina.modulos.all()}
        for phase in data['phases']:
            module, _ = Modulo.objects.update_or_create(
                disciplina=disciplina, ordem=phase['number'],
                defaults={'titulo': phase['title'], 'descricao': phase.get('description', '')},
            )
            for exercise in (e for e in data['exercises'] if e['phase'] == phase['number']):
                phase_obj, _ = Fase.objects.update_or_create(
                    modulo=module, ordem=exercise['exercise_number'],
                    defaults={
                        'titulo': exercise['title'],
                        'tipo': 'quiz',
                        'xp_recompensa': exercise.get('completion', {}).get('xp', 30),
                    },
                )
                question, _ = Questao.objects.update_or_create(
                    codigo_fonte=exercise['id'],
                    defaults={
                        'fase': phase_obj,
                        'enunciado': exercise['challenge']['prompt'],
                        'explicacao_erro': exercise['challenge'].get('answer', {}).get('hint', ''),
                        'tipo_resposta': 'numeric' if exercise['challenge']['answer']['type'] != 'choice' else 'choice',
                        'dados_dinamicos': exercise,
                    },
                )
                answer = exercise['challenge']['answer']
                if answer['type'] == 'choice':
                    choices = answer.get('choices', [])
                    existing = list(question.opcoes.order_by('ordem', 'id'))
                    for index, text in enumerate(choices):
                        if index < len(existing):
                            option = existing[index]
                            option.texto = text
                            option.e_correta = index == answer['correct']
                            option.ordem = index + 1
                            option.save()
                        else:
                            Opcao.objects.create(
                                questao=question, texto=text,
                                e_correta=index == answer['correct'], ordem=index + 1,
                            )
                    for option in existing[len(choices):]:
                        option.delete()
                else:
                    question.opcoes.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'Química 2 importada: {len(data["phases"])} módulos e {len(data["exercises"])} exercícios. A disciplina permanece inativa até publicação.'
        ))
