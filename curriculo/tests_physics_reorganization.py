"""Testes de preservação de dados na reorganização dos jogos de Física."""
from django.contrib.auth.models import User
from django.test import TestCase

from gamificacao.models import (
    PerfilUsuario,
    ProgressoFase,
    RespostaTentativa,
    TentativaFase,
)
from .models import Disciplina, Fase, Materia, Modulo, Questao
from scripts.reorganizar_jogos_fisica import apply_plan


class PhysicsReorganizationPreservationTests(TestCase):
    def test_apply_plan_preserves_existing_rewards_and_progress(self):
        # A matéria Física é criada por uma migração de dados do projeto.
        materia = Materia.objects.get(slug="fisica")
        legacy = Disciplina.objects.create(
            nome="Física antiga de teste",
            slug="fisica-legado-preservacao-teste",
            materia=materia,
            ativo=False,
        )
        game_slug = "fisica-1-preservacao-teste"
        game = Disciplina.objects.create(
            nome="Física 1 de teste",
            slug=game_slug,
            materia=materia,
        )
        module = Modulo.objects.create(
            disciplina=game,
            titulo="Cinemática",
            ordem=1,
        )
        phase = Fase.objects.create(
            modulo=module,
            titulo="Fase original",
            ordem=1,
            xp_recompensa=75,
            moedas_recompensa=12,
        )
        question = Questao.objects.create(
            fase=phase,
            enunciado="Enunciado preservado",
            tipo_resposta="numeric",
            codigo_fonte="fisica1-preservacao-001",
        )

        user = User.objects.create_user(username="aluno-preservacao")
        profile = PerfilUsuario.objects.get(usuario=user)
        progress = ProgressoFase.objects.create(
            perfil=profile,
            fase=phase,
            concluida=True,
            erros=2,
            tentativas=7,
            melhor_aproveitamento=85,
        )
        attempt = TentativaFase.objects.create(
            perfil=profile,
            fase=phase,
            fase_titulo_snapshot="Fase original",
        )
        RespostaTentativa.objects.create(
            tentativa=attempt,
            questao=question,
            texto_questao_snapshot="Enunciado histórico",
            correta=False,
        )

        plan = [{
            "number": 1,
            "slug": game_slug,
            "name": "Física 1 de teste",
            "description": "Jogo Física 1 de teste",
            "exercise_count": 1,
            "topic_count": 1,
            "topics": [{
                "number": 1,
                "title": "Cinemática",
                "description": "Tópico de teste",
                "phases": [{
                    "order": 1,
                    "question_id": question.pk,
                    "exercise": {"title": "Fase reorganizada"},
                }],
            }],
        }]

        apply_plan(
            materia, legacy, plan,
            Disciplina, Modulo, Fase, Questao,
        )

        phase.refresh_from_db()
        progress.refresh_from_db()
        question.refresh_from_db()

        self.assertEqual(phase.xp_recompensa, 75)
        self.assertEqual(phase.moedas_recompensa, 12)
        self.assertTrue(progress.concluida)
        self.assertEqual(progress.erros, 2)
        self.assertEqual(progress.tentativas, 7)
        self.assertEqual(progress.melhor_aproveitamento, 85)
        self.assertEqual(question.fase_id, phase.pk)
        self.assertEqual(RespostaTentativa.objects.filter(questao=question).count(), 1)
