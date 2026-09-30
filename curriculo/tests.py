import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Disciplina, Fase, Modulo, Opcao, Questao
from gamificacao.models import ProgressoFase, TentativaFase


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
            reverse("redirecionamento_inicial"),
            fetch_redirect_response=False,
        )

        dashboard_response = self.client.get(
            reverse("redirecionamento_inicial")
        )

        self.assertRedirects(
            dashboard_response,
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


@override_settings(DEBUG=True)
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
            reverse("redirecionamento_inicial"),
            fetch_redirect_response=False,
        )

        dashboard_response = self.client.get(
            reverse("redirecionamento_inicial")
        )

        self.assertRedirects(
            dashboard_response,
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
            reverse("redirecionamento_inicial"),
            fetch_redirect_response=False,
        )

        dashboard_response = self.client.get(
            reverse("redirecionamento_inicial")
        )

        self.assertRedirects(
            dashboard_response,
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


class PublicacaoTrilhaTests(AutenticacaoBaseTests):

    def test_publicar_trilha_pronta(self):
        professor = self.criar_usuario(
            username="professor_publicacao"
        )

        professor.perfil.tipo = "professor"
        professor.perfil.save(
            update_fields=["tipo"]
        )

        trilha = Disciplina.objects.create(
            nome="Trilha Publicável",
            slug="trilha-publicavel-teste",
            ativo=False,
            autor=professor,
        )

        modulo = Modulo.objects.create(
            disciplina=trilha,
            titulo="Módulo 1",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase 1",
            ordem=1,
        )

        questao = Questao.objects.create(
            fase=fase,
            enunciado="Quanto é 2 + 2?",
        )

        Opcao.objects.create(
            questao=questao,
            texto="4",
            e_correta=True,
        )

        self.client.login(
            username=professor.username,
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse(
                "alternar_publicacao",
                args=[trilha.id],
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard_professor"),
        )

        trilha.refresh_from_db()

        self.assertTrue(
            trilha.ativo
        )

    def test_nao_publica_trilha_vazia(self):
        professor = self.criar_usuario(
            username="professor_vazio"
        )

        professor.perfil.tipo = "professor"
        professor.perfil.save(
            update_fields=["tipo"]
        )

        trilha = Disciplina.objects.create(
            nome="Trilha Vazia",
            slug="trilha-vazia-teste",
            ativo=False,
            autor=professor,
        )

        self.client.login(
            username=professor.username,
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse(
                "alternar_publicacao",
                args=[trilha.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "editar_trilha",
                args=[trilha.id],
            )
        )

        trilha.refresh_from_db()

        self.assertFalse(
            trilha.ativo
        )


class ProgressaoEVidasTests(AutenticacaoBaseTests):

    def setUp(self):
        self.aluno = self.criar_usuario(
            username="aluno_progressao"
        )

        self.trilha = Disciplina.objects.create(
            nome="Trilha de Teste",
            slug="trilha-de-teste-gamificacao",
            ativo=True,
            autor=self.aluno,
        )

        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo",
            ordem=1,
        )

        self.fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase",
            ordem=1,
            xp_recompensa=100,
            moedas_recompensa=20,
        )

        self.questao = Questao.objects.create(
            fase=self.fase,
            enunciado="Qual é a resposta?",
            explicacao_erro="Revise o conceito.",
        )

        self.correta = Opcao.objects.create(
            questao=self.questao,
            texto="Correta",
            e_correta=True,
        )

        self.incorreta = Opcao.objects.create(
            questao=self.questao,
            texto="Incorreta",
            e_correta=False,
        )

        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

    def _finalizar(self, opcao_id):
        return self.client.post(
            reverse(
                "finalizar_fase",
                args=[self.fase.id],
            ),
            data=json.dumps({
                "respostas": [
                    {
                        "questao_id": self.questao.id,
                        "opcao_id": opcao_id,
                    }
                ]
            }),
            content_type="application/json",
        )

    def test_tentativa_reprovada_consume_uma_vida_e_gera_historico(self):
        response = self._finalizar(
            self.incorreta.id
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.aluno.refresh_from_db()

        self.assertEqual(
            self.aluno.perfil.vidas,
            self.aluno.perfil.VIDAS_MAXIMAS - 1,
        )

        self.assertEqual(
            TentativaFase.objects.filter(
                perfil=self.aluno.perfil,
                fase=self.fase,
            ).count(),
            1,
        )

        progresso = ProgressoFase.objects.get(
            perfil=self.aluno.perfil,
            fase=self.fase,
        )

        self.assertFalse(
            progresso.concluida
        )

    def test_fase_concluida_concede_recompensa_sem_consumir_vida(self):
        response = self._finalizar(
            self.correta.id
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.aluno.refresh_from_db()

        self.assertEqual(
            self.aluno.perfil.vidas,
            self.aluno.perfil.VIDAS_MAXIMAS,
        )

        self.assertEqual(
            self.aluno.perfil.xp_total,
            100,
        )

        self.assertEqual(
            self.aluno.perfil.moedas,
            20,
        )

        self.assertTrue(
            ProgressoFase.objects.get(
                perfil=self.aluno.perfil,
                fase=self.fase,
            ).concluida
        )

    def test_sem_vidas_bloqueia_nova_tentativa(self):
        self.aluno.perfil.vidas = 0
        self.aluno.perfil.save(
            update_fields=["vidas"]
        )

        response = self._finalizar(
            self.incorreta.id
        )

        self.assertEqual(
            response.status_code,
            409,
        )

        self.assertIn(
            "sem vidas",
            response.json()["msg"].lower()
        )

    def test_revisao_fica_disponivel_apos_tentativa_reprovada(self):
        response = self._finalizar(
            self.incorreta.id
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response = self.client.get(
            reverse(
                "revisao_fase",
                args=[self.fase.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Revisão: Fase"
        )

class EstudioConteudoTests(AutenticacaoBaseTests):
    def setUp(self):
        self.professor = self.criar_usuario(
            username="criador",
        )
        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(update_fields=["tipo"])

        self.trilha = Disciplina.objects.create(
            nome="Jogo de Teste",
            slug="jogo-de-teste",
            ativo=False,
            autor=self.professor,
        )

        self.client.login(
            username="criador",
            password="SenhaForte123!",
        )

    def test_editor_exibe_fluxo_e_contadores(self):
        response = self.client.get(
            reverse(
                "editar_trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Estrutura do jogo")
        self.assertContains(response, "Mapa da jornada")
        self.assertContains(response, "Módulos")

    def test_professor_pode_criar_editar_e_excluir_modulo(self):
        response = self.client.post(
            reverse(
                "ajax_criar_modulo",
                args=[self.trilha.id],
            ),
            {
                "titulo": "Base",
                "descricao": "Fundamentos",
                "ordem": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        modulo = Modulo.objects.get(
            disciplina=self.trilha,
            titulo="Base",
        )

        response = self.client.post(
            reverse(
                "ajax_editar_modulo",
                args=[modulo.id],
            ),
            {
                "titulo": "Base revisada",
                "descricao": "Novo resumo",
                "ordem": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        modulo.refresh_from_db()
        self.assertEqual(modulo.titulo, "Base revisada")
        self.assertEqual(modulo.ordem, 2)

        response = self.client.post(
            reverse(
                "ajax_excluir_modulo",
                args=[modulo.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Modulo.objects.filter(id=modulo.id).exists()
        )

    def test_professor_pode_criar_editar_e_excluir_fase(self):
        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo 1",
            ordem=1,
        )

        response = self.client.post(
            reverse(
                "ajax_criar_fase",
                args=[self.trilha.id],
            ),
            {
                "modulo_id": modulo.id,
                "titulo": "Fase 1",
                "ordem": 1,
                "tipo": "quiz",
                "xp_recompensa": 50,
                "moedas_recompensa": 10,
                "deslocamento_y": 0,
            },
        )

        self.assertEqual(response.status_code, 200)
        fase = Fase.objects.get(
            modulo=modulo,
            titulo="Fase 1",
        )

        response = self.client.post(
            reverse(
                "ajax_editar_fase",
                args=[fase.id],
            ),
            {
                "modulo_id": modulo.id,
                "titulo": "Fase revisada",
                "ordem": 2,
                "tipo": "desafio",
                "xp_recompensa": 80,
                "moedas_recompensa": 15,
                "deslocamento_y": 70,
            },
        )

        self.assertEqual(response.status_code, 200)
        fase.refresh_from_db()
        self.assertEqual(fase.titulo, "Fase revisada")
        self.assertEqual(fase.tipo, "desafio")
        self.assertEqual(fase.deslocamento_y, 70)

        response = self.client.post(
            reverse(
                "ajax_excluir_fase",
                args=[fase.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Fase.objects.filter(id=fase.id).exists()
        )

