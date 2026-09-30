from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Disciplina


class AutenticacaoBaseTests(TestCase):
    def criar_usuario(
        self,
        username="teste",
        password="SenhaForte123!",
        is_staff=False,
        is_superuser=False,
    ):
        return User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )


class CadastroUsuarioTests(AutenticacaoBaseTests):
    def test_cadastro_cria_usuario_e_perfil_com_papel_aluno(self):
        response = self.client.post(
            reverse("cadastro_usuario"),
            {
                "username": "novo_aluno",
                "first_name": "Novo",
                "last_name": "Aluno",
                "email": "novo.aluno@example.com",
                "password1": "SenhaForte123!",
                "password2": "SenhaForte123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard_aluno"),
        )

        usuario = User.objects.get(
            username="novo_aluno"
        )

        self.assertEqual(
            usuario.perfil.tipo,
            "aluno",
        )

        self.assertTrue(
            usuario.is_active
        )


class LoginTests(AutenticacaoBaseTests):
    def test_usuario_nao_autenticado_e_redirecionado_para_login(self):
        response = self.client.get(
            reverse("dashboard_aluno")
        )

        self.assertRedirects(
            response,
            (
                f"{reverse('login')}"
                f"?next={reverse('dashboard_aluno')}"
            ),
        )

    def test_login_redireciona_para_painel_do_papel_oficial(self):
        usuario = self.criar_usuario()

        self.client.login(
            username=usuario.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse("redirecionamento_inicial")
        )

        self.assertRedirects(
            response,
            reverse("dashboard_aluno"),
        )


class ModoTestePapelTests(AutenticacaoBaseTests):
    def test_staff_pode_alternar_para_professor_sem_alterar_perfil_oficial(self):
        usuario = self.criar_usuario(
            username="desenvolvedor",
            is_staff=True,
        )

        self.client.login(
            username=usuario.username,
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("alternar_papel")
        )

        self.assertRedirects(
            response,
            reverse("dashboard_professor"),
        )

        usuario.refresh_from_db()

        self.assertEqual(
            usuario.perfil.tipo,
            "aluno",
        )

        response = self.client.post(
            reverse("alternar_papel")
        )

        self.assertRedirects(
            response,
            reverse("dashboard_aluno"),
        )

        usuario.refresh_from_db()

        self.assertEqual(
            usuario.perfil.tipo,
            "aluno",
        )

    def test_usuario_comum_nao_pode_usar_modo_de_teste(self):
        usuario = self.criar_usuario()

        self.client.login(
            username=usuario.username,
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("alternar_papel")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        usuario.refresh_from_db()

        self.assertEqual(
            usuario.perfil.tipo,
            "aluno",
        )


class AutorizacaoDeConteudoTests(AutenticacaoBaseTests):
    def test_professor_oficial_ve_apenas_as_proprias_trilhas(self):
        professor = self.criar_usuario(
            username="professor",
        )
        outro_usuario = self.criar_usuario(
            username="outro",
        )

        professor.perfil.tipo = "professor"
        professor.perfil.save(
            update_fields=["tipo"]
        )

        propria = Disciplina.objects.create(
            nome="Minha Trilha",
            slug="minha-trilha",
            ativo=False,
            autor=professor,
        )

        Disciplina.objects.create(
            nome="Trilha de Outro",
            slug="trilha-de-outro",
            ativo=False,
            autor=outro_usuario,
        )

        self.client.login(
            username=professor.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse("dashboard_professor")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            propria.nome,
        )

        self.assertNotContains(
            response,
            "Trilha de Outro",
        )


class PublicacaoTests(AutenticacaoBaseTests):
    def test_aluno_nao_enxerga_trilha_em_rascunho(self):
        aluno = self.criar_usuario()

        Disciplina.objects.create(
            nome="Rascunho",
            slug="rascunho",
            ativo=False,
            autor=aluno,
        )

        self.client.login(
            username=aluno.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse("dashboard_aluno")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            "Rascunho",
        )
