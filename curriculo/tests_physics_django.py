"""Testes Django de integração para resposta numérica, choice e histórico.

Requer que models_integration.patch e urls_integration.patch tenham sido aplicados.
"""
import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from gamificacao.models import RespostaTentativa, TentativaFase


class PhysicsPlayerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='physics-test', password='test-password')
        self.materia = Materia.objects.create(nome='Física', slug='fisica-test')
        self.disciplina = Disciplina.objects.create(nome='Física', slug='fisica-test', materia=self.materia, ativo=True)
        self.modulo = Modulo.objects.create(disciplina=self.disciplina, titulo='Módulo 1', ordem=1)
        self.fase = Fase.objects.create(modulo=self.modulo, titulo='Cinemática', ordem=1)
        self.client.force_login(self.user)

    def _numeric_question(self):
        data = {
            'id': 'test-numeric', 'title': 'MRU', 'topic': 'MRU', 'context': 'Carrinho em pista.',
            'simulation': {'scene': 'mru_track', 'description': 'Pista', 'show_vectors': True,
                           'show_live_readouts': True, 'parameters': [
                               {'key': 'v', 'label': 'Velocidade', 'value': 2, 'unit': 'm/s', 'min': 0, 'max': 10, 'step': 1, 'hint': ''},
                               {'key': 't', 'label': 'Tempo', 'value': 3, 'unit': 's', 'min': 0, 'max': 10, 'step': 1, 'hint': ''},
                               {'key': 'x0', 'label': 'Posição inicial', 'value': 1, 'unit': 'm', 'min': 0, 'max': 10, 'step': 1, 'hint': ''}]},
            'challenge': {'prompt': 'Qual a posição?', 'answer': {'type': 'numeric', 'formula': 'mru_position', 'unit': 'm', 'tolerance': .02, 'digits': 2, 'display_unit': 'm'}, 'hint': 'Use x=x0+vt.', 'solution': 'Some x0 e vt.'},
            'completion': {'xp': 30, 'mastery_tag': 'MRU'},
        }
        return Questao.objects.create(fase=self.fase, enunciado='Qual a posição?', tipo_resposta='numeric', codigo_fonte='test-numeric', dados_dinamicos=data)

    def test_numeric_answer_saves_parameters_and_feedback(self):
        question = self._numeric_question()
        self.client.get(reverse('physics_player', args=[self.fase.id]))
        response = self.client.post(reverse('physics_check_answer', args=[self.fase.id]), data=json.dumps({
            'questao_id': question.id, 'valor': 7, 'parameters': {'v': 2, 't': 3, 'x0': 1}
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['correct'])
        history = RespostaTentativa.objects.get(questao=question)
        self.assertEqual(history.parametros_snapshot, {'v': 2, 't': 3, 'x0': 1})
        self.assertEqual(history.resposta_correta_snapshot['value'], 7)
        self.assertEqual(history.tipo_resposta_snapshot, 'numeric')

    def test_choice_answer_preserves_option_snapshot(self):
        question = Questao.objects.create(fase=self.fase, enunciado='Qual?', tipo_resposta='choice', codigo_fonte='test-choice', dados_dinamicos={
            'title': 'Inércia', 'topic': 'Inércia', 'context': 'Ônibus.',
            'simulation': {'scene': 'inertia_bus', 'parameters': [], 'show_vectors': True, 'show_live_readouts': True},
            'challenge': {'prompt': 'Qual?', 'answer': {'type': 'choice', 'correct': 0, 'options': ['A', 'B', 'C'], 'explanation': 'Explicação.'}},
            'completion': {'xp': 30, 'mastery_tag': 'Inércia'},
        })
        options = [Opcao.objects.create(questao=question, texto=t, ordem=i+1, e_correta=(i == 0)) for i, t in enumerate(['A','B','C'])]
        self.client.get(reverse('physics_player', args=[self.fase.id]))
        response = self.client.post(reverse('physics_check_answer', args=[self.fase.id]), data=json.dumps({'questao_id': question.id, 'opcao_id': options[0].id}), content_type='application/json')
        self.assertTrue(response.json()['correct'])
        history = RespostaTentativa.objects.get(questao=question)
        self.assertEqual(history.texto_opcao_snapshot, 'A')
        self.assertEqual(history.resposta_snapshot['text'], 'A')