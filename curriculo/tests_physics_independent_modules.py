"""Testes da progressão independente entre módulos de um jogo."""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from .models import Disciplina, Fase, Modulo
from .views import fase_esta_liberada
from gamificacao.models import ProgressoFase, ProgressoModulo


class ModulosIndependentesTests(TestCase):
    def setUp(self):
        self.aluno = User.objects.create_user(
            username="aluno_modulos_independentes",
            password="SenhaForte123!",
        )
        self.perfil = self.aluno.perfil
        self.jogo = Disciplina.objects.create(
            nome="Física 3",
            slug="fisica-3-independencia",
            ativo=True,
            autor=self.aluno,
        )
        self.modulo_1 = Modulo.objects.create(
            disciplina=self.jogo,
            titulo="Módulo 1",
            ordem=1,
        )
        self.modulo_2 = Modulo.objects.create(
            disciplina=self.jogo,
            titulo="Módulo 2",
            ordem=2,
        )
        self.fase_1_modulo_1 = Fase.objects.create(
            modulo=self.modulo_1,
            titulo="Fase 1 do módulo 1",
            ordem=1,
        )
        self.fase_1_modulo_2 = Fase.objects.create(
            modulo=self.modulo_2,
            titulo="Fase 1 do módulo 2",
            ordem=1,
        )
        self.fase_2_modulo_2 = Fase.objects.create(
            modulo=self.modulo_2,
            titulo="Fase 2 do módulo 2",
            ordem=2,
        )
        ProgressoModulo.objects.create(
            perfil=self.perfil,
            modulo=self.modulo_2,
            desbloqueado=False,
        )
        self.request = RequestFactory().get("/")
        self.request.user = self.aluno
        self.request.session = {}

    def test_primeira_fase_de_qualquer_modulo_fica_disponivel(self):
        self.assertTrue(
            fase_esta_liberada(self.request, self.fase_1_modulo_2)
        )

    def test_fases_seguem_sequencia_dentro_do_proprio_modulo(self):
        self.assertFalse(
            fase_esta_liberada(self.request, self.fase_2_modulo_2)
        )
        ProgressoFase.objects.create(
            perfil=self.perfil,
            fase=self.fase_1_modulo_2,
            concluida=True,
        )
        self.assertTrue(
            fase_esta_liberada(self.request, self.fase_2_modulo_2)
        )

    def test_modulo_anterior_nao_precisa_ser_concluido(self):
        self.assertFalse(
            ProgressoFase.objects.filter(
                perfil=self.perfil,
                fase__modulo=self.modulo_1,
                concluida=True,
            ).exists()
        )
        self.assertTrue(
            fase_esta_liberada(self.request, self.fase_1_modulo_2)
        )
