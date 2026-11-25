from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao
from curriculo.rewards import conceder_moedas_por_questao
from gamificacao.models import PerfilUsuario, TentativaFase, RespostaTentativa


class CoinRewardTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="coin-test", password="test")
        self.profile = PerfilUsuario.objects.get(usuario=user)
        subject = Materia.objects.create(nome="Matemática", slug="matematica-test")
        game = Disciplina.objects.create(
            nome="Matemática teste", slug="matematica-test-game",
            materia=subject, ativo=True,
        )
        self.module = Modulo.objects.create(disciplina=game, titulo="Módulo 1", ordem=1)
        self.questions = []
        for phase_order in range(1, 4):
            phase = Fase.objects.create(modulo=self.module, titulo=f"Fase {phase_order}", ordem=phase_order)
            self.questions.append(Questao.objects.create(
                fase=phase, enunciado=f"Questão {phase_order}",
                dados_dinamicos={"completion": {"xp": 10}},
            ))

    def _finish_answer(self, question, correct=True):
        attempt = TentativaFase.objects.create(
            perfil=self.profile, fase=question.fase,
            fase_titulo_snapshot=question.fase.titulo,
            total_questoes=1, finalizada_em=timezone.now(),
        )
        answer = RespostaTentativa.objects.create(
            tentativa=attempt, questao=question,
            texto_questao_snapshot=question.enunciado,
            correta=correct,
        )
        with self.captureOnCommitCallbacks(execute=True):
            from django.db import transaction
            with transaction.atomic():
                coins = conceder_moedas_por_questao(attempt, [answer])
        return attempt, coins

    def test_coin_value_follows_question_position(self):
        _, coins = self._finish_answer(self.questions[1])
        self.assertEqual(coins, 2)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.moedas, 2)

    def test_same_question_is_rewarded_only_once(self):
        self._finish_answer(self.questions[1])
        _, second_reward = self._finish_answer(self.questions[1])
        self.assertEqual(second_reward, 0)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.moedas, 2)

    def test_different_questions_accumulate_their_positions(self):
        self._finish_answer(self.questions[0])
        self._finish_answer(self.questions[2])
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.moedas, 4)

    def test_incorrect_answer_does_not_earn_coins(self):
        _, coins = self._finish_answer(self.questions[0], correct=False)
        self.assertEqual(coins, 0)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.moedas, 0)
