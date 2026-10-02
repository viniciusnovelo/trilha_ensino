import json
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Disciplina, Fase, Materia, Modulo, Opcao, Questao
from gamificacao.models import ProgressoFase, ProgressoModulo, TentativaFase


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

    def test_resposta_incorreta_retorna_explicacao_e_resposta_correta(self):
        response = self.client.post(
            reverse(
                "verificar_resposta",
                args=[self.fase.id],
            ),
            data=json.dumps({
                "questao_id": self.questao.id,
                "opcao_id": self.incorreta.id,
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        dados = response.json()

        self.assertFalse(
            dados["correta"],
        )

        self.assertEqual(
            dados["explicacao"],
            "Revise o conceito.",
        )

        self.assertEqual(
            dados["opcao_correta"]["texto"],
            "Correta",
        )

    def test_feedback_final_preserva_raciocinio_em_etapas(self):
        self.questao.explicacao_erro = (
            "Como pensar: substitua o valor de x na expressão.\n"
            "Passo a passo:\n"
            "1. Substitua x pelo valor informado.\n"
            "2. Faça as operações na ordem.\n"
            "Conclusão: confira o resultado encontrado."
        )
        self.questao.save(
            update_fields=["explicacao_erro"]
        )

        response = self._finalizar(
            self.correta.id
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        feedback = response.json()["feedback_questoes"][0]

        self.assertIn(
            "Como pensar:",
            feedback["explicacao"],
        )

        self.assertIn(
            "Passo a passo:",
            feedback["explicacao"],
        )

        self.assertIn(
            "Conclusão:",
            feedback["explicacao"],
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

        dados = response.json()

        self.assertIn(
            "feedback_questoes",
            dados,
        )

        self.assertEqual(
            len(dados["feedback_questoes"]),
            1,
        )

        feedback = dados["feedback_questoes"][0]

        self.assertTrue(
            feedback["correta"],
        )

        self.assertEqual(
            feedback["resposta_aluno"],
            "Correta",
        )

        self.assertEqual(
            feedback["resposta_correta"],
            "Correta",
        )

        self.assertEqual(
            feedback["explicacao"],
            "Revise o conceito.",
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

        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo já criado",
            ordem=1,
        )

        response = self.client.get(
            reverse(
                "editar_trilha",
                args=[self.trilha.id],
            )
        )

        self.assertContains(
            response,
            "Módulo já criado",
        )
        self.assertContains(
            response,
            "Editar módulo",
        )
        self.assertContains(
            response,
            "Excluir módulo",
        )

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



    def test_dashboard_professor_exibe_trilha_e_estrutura_criada(self):
        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo visível",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase visível",
            ordem=1,
        )

        questao = Questao.objects.create(
            fase=fase,
            enunciado="Atividade visível",
        )

        Opcao.objects.create(
            questao=questao,
            texto="Resposta A",
            e_correta=True,
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
            self.trilha.nome,
        )

        self.assertContains(
            response,
            modulo.titulo,
        )

        self.assertContains(
            response,
            "1 módulo",
        )

        self.assertContains(
            response,
            "1 fase",
        )

        self.assertContains(
            response,
            "1 questão",
        )

    def test_editor_previsualiza_fase_com_link_para_a_fase_real(self):
        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Preview",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase clicável",
            ordem=1,
        )

        response = self.client.get(
            reverse(
                "editar_trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Fase clicável",
        )

        self.assertContains(
            response,
            reverse(
                "fase_detalhe",
                args=[fase.id],
            ),
        )

    def test_editor_exibe_e_gerencia_questoes_criadas(self):
        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Atividades",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase Atividades",
            ordem=1,
        )

        questao = Questao.objects.create(
            fase=fase,
            enunciado="Atividade que deve aparecer",
            explicacao_erro="Feedback de revisão.",
        )

        Opcao.objects.create(
            questao=questao,
            texto="Alternativa A",
            e_correta=False,
        )

        Opcao.objects.create(
            questao=questao,
            texto="Alternativa B",
            e_correta=True,
        )

        response = self.client.get(
            reverse(
                "editar_trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Atividade que deve aparecer",
        )

        self.assertContains(
            response,
            "Editar questão",
        )

        self.assertContains(
            response,
            "Excluir questão",
        )

    def test_professor_pode_criar_editar_e_excluir_questao(self):
        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Questões",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase Questões",
            ordem=1,
        )

        response = self.client.post(
            reverse("ajax_criar_questao"),
            {
                "fase_id": fase.id,
                "enunciado": "Quanto é 2 + 2?",
                "explicacao_erro": "Revise a soma.",
                "op_texto_0": "3",
                "op_texto_1": "4",
                "op_texto_2": "5",
                "op_texto_3": "6",
                "op_correta": "1",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        questao = Questao.objects.get(
            fase=fase,
            enunciado="Quanto é 2 + 2?",
        )

        self.assertEqual(
            questao.opcoes.count(),
            4,
        )

        self.assertEqual(
            questao.opcoes.filter(e_correta=True).count(),
            1,
        )

        response = self.client.post(
            reverse(
                "ajax_editar_questao",
                args=[questao.id],
            ),
            {
                "enunciado": "Quanto é 3 + 2?",
                "explicacao_erro": "Revise a soma de números naturais.",
                "op_texto_0": "4",
                "op_texto_1": "5",
                "op_texto_2": "6",
                "op_correta": "1",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        questao.refresh_from_db()

        self.assertEqual(
            questao.enunciado,
            "Quanto é 3 + 2?",
        )

        self.assertEqual(
            questao.opcoes.count(),
            3,
        )

        self.assertEqual(
            questao.opcoes.filter(e_correta=True).count(),
            1,
        )

        self.assertEqual(
            questao.opcoes.get(e_correta=True).texto,
            "5",
        )

        response = self.client.post(
            reverse(
                "ajax_excluir_questao",
                args=[questao.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            Questao.objects.filter(
                id=questao.id
            ).exists()
        )


class ProgressaoPorModulosTests(AutenticacaoBaseTests):
    def setUp(self):
        self.aluno = self.criar_usuario(
            username="aluno_modulos",
        )

        self.professor = self.criar_usuario(
            username="professor_modulos",
        )

        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(
            update_fields=["tipo"]
        )

        self.trilha = Disciplina.objects.create(
            nome="Jornada por Módulos",
            slug="jornada-por-modulos",
            ativo=True,
            autor=self.professor,
        )

        self.modulo_1 = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo 1",
            ordem=1,
        )

        self.modulo_2 = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo 2",
            ordem=2,
        )

        self.modulo_3 = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo 3",
            ordem=3,
        )

        self.modulo_4 = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo 4",
            ordem=4,
        )

        self.fase_1 = Fase.objects.create(
            modulo=self.modulo_1,
            titulo="Fase 1",
            ordem=1,
        )

        self.fase_2 = Fase.objects.create(
            modulo=self.modulo_2,
            titulo="Fase 2",
            ordem=1,
        )

        self.fase_3 = Fase.objects.create(
            modulo=self.modulo_3,
            titulo="Fase 3",
            ordem=1,
        )

        self.fase_4 = Fase.objects.create(
            modulo=self.modulo_4,
            titulo="Fase 4",
            ordem=1,
        )

        self.questao_1 = Questao.objects.create(
            fase=self.fase_1,
            enunciado="Qual é a resposta da fase 1?",
        )

        self.opcao_correta_1 = Opcao.objects.create(
            questao=self.questao_1,
            texto="Correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=self.questao_1,
            texto="Incorreta",
            e_correta=False,
        )

        self.questao_2 = Questao.objects.create(
            fase=self.fase_2,
            enunciado="Qual é a resposta da fase 2?",
        )

        Opcao.objects.create(
            questao=self.questao_2,
            texto="Correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=self.questao_2,
            texto="Incorreta",
            e_correta=False,
        )

        self.questao_3 = Questao.objects.create(
            fase=self.fase_3,
            enunciado="Qual é a resposta da fase 3?",
        )

        self.questao_4 = Questao.objects.create(
            fase=self.fase_4,
            enunciado="Qual é a resposta da fase 4?",
        )

        Opcao.objects.create(
            questao=self.questao_3,
            texto="Correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=self.questao_3,
            texto="Incorreta",
            e_correta=False,
        )

        Opcao.objects.create(
            questao=self.questao_4,
            texto="Correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=self.questao_4,
            texto="Incorreta",
            e_correta=False,
        )

        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

    def finalizar_fase(
        self,
        fase,
        questao,
        opcao,
    ):
        return self.client.post(
            reverse(
                "finalizar_fase",
                args=[fase.id],
            ),
            data=json.dumps({
                "respostas": [
                    {
                        "questao_id": questao.id,
                        "opcao_id": opcao.id,
                    }
                ]
            }),
            content_type="application/json",
        )

    def test_primeiro_modulo_e_liberado_e_segundo_fica_bloqueado(self):
        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        modulos = response.context["modulos"]

        self.assertTrue(
            modulos[0].desbloqueado,
        )

        self.assertEqual(
            modulos[0].status,
            "atual",
        )

        self.assertFalse(
            modulos[1].desbloqueado,
        )

        self.assertEqual(
            modulos[1].status,
            "bloqueado",
        )

        progresso = ProgressoModulo.objects.get(
            perfil=self.aluno.perfil,
            modulo=self.modulo_1,
        )

        self.assertTrue(
            progresso.desbloqueado,
        )

    def test_fase_do_modulo_seguinte_nao_pode_ser_acessada_antes(self):
        response = self.client.get(
            reverse(
                "fase_detalhe",
                args=[self.fase_2.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "trilha",
                args=[self.trilha.id],
            ),
        )

    def test_conclusao_do_modulo_desbloqueia_automaticamente_o_proximo(self):
        response = self.finalizar_fase(
            self.fase_1,
            self.questao_1,
            self.opcao_correta_1,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        dados = response.json()

        self.assertTrue(
            dados["modulo_concluido"],
        )

        self.assertTrue(
            dados["proximo_modulo_desbloqueado"],
        )

        self.assertEqual(
            dados["proximo_modulo_id"],
            self.modulo_2.id,
        )

        progresso = ProgressoModulo.objects.get(
            perfil=self.aluno.perfil,
            modulo=self.modulo_2,
        )

        self.assertTrue(
            progresso.desbloqueado,
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        modulos = response.context["modulos"]

        self.assertEqual(
            modulos[0].status,
            "concluido",
        )

        self.assertEqual(
            modulos[1].status,
            "atual",
        )

        self.assertTrue(
            modulos[1].desbloqueado,
        )

        fase_2 = next(
            fase
            for fase in modulos[1].fases.all()
        )

        self.assertEqual(
            fase_2.status,
            "atual",
        )

        response = self.client.get(
            reverse(
                "fase_detalhe",
                args=[self.fase_2.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_modulo_seguinte_permanece_bloqueado_apos_conclusao_parcial(self):
        segunda_fase = Fase.objects.create(
            modulo=self.modulo_1,
            titulo="Fase 1B",
            ordem=2,
        )

        questao = Questao.objects.create(
            fase=segunda_fase,
            enunciado="Pergunta da fase 1B",
        )

        Opcao.objects.create(
            questao=questao,
            texto="Correta",
            e_correta=True,
        )

        self.finalizar_fase(
            self.fase_1,
            self.questao_1,
            self.opcao_correta_1,
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        modulos = response.context["modulos"]

        self.assertEqual(
            modulos[0].status,
            "atual",
        )

        self.assertEqual(
            modulos[0].fases_concluidas,
            1,
        )

        self.assertEqual(
            modulos[0].percentual_progresso,
            50,
        )

        self.assertEqual(
            modulos[1].status,
            "bloqueado",
        )

        self.assertFalse(
            modulos[1].desbloqueado,
        )

    def test_conclusao_dos_modulos_em_cadeia_libera_o_modulo_4(self):
        self.finalizar_fase(
            self.fase_1,
            self.questao_1,
            self.opcao_correta_1,
        )

        segunda_opcao_correta = (
            self.questao_2.opcoes
            .filter(
                e_correta=True,
            )
            .first()
        )

        self.assertIsNotNone(
            segunda_opcao_correta,
        )

        segunda_resposta = self.finalizar_fase(
            self.fase_2,
            self.questao_2,
            segunda_opcao_correta,
        )

        self.assertEqual(
            segunda_resposta.status_code,
            200,
        )

        self.assertTrue(
            segunda_resposta.json()["modulo_concluido"],
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        modulos = response.context["modulos"]

        self.assertEqual(
            modulos[1].status,
            "concluido",
        )

        self.assertTrue(
            modulos[2].desbloqueado,
        )

        self.assertEqual(
            modulos[2].status,
            "atual",
        )

        terceira_opcao_correta = (
            self.questao_3.opcoes
            .filter(
                e_correta=True,
            )
            .first()
        )

        terceira_resposta = self.finalizar_fase(
            self.fase_3,
            self.questao_3,
            terceira_opcao_correta,
        )

        self.assertEqual(
            terceira_resposta.status_code,
            200,
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        modulos = response.context["modulos"]

        self.assertEqual(
            modulos[2].status,
            "concluido",
        )

        self.assertTrue(
            modulos[3].desbloqueado,
        )

        self.assertEqual(
            modulos[3].status,
            "atual",
        )


class PreviewProfessorTests(AutenticacaoBaseTests):
    def setUp(self):
        self.professor = self.criar_usuario(
            username="professor_preview",
        )

        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(
            update_fields=["tipo"]
        )

        self.trilha = Disciplina.objects.create(
            nome="Trilha de Preview",
            slug="trilha-de-preview",
            ativo=False,
            autor=self.professor,
        )

        self.modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Preview",
            ordem=1,
        )

        self.fase = Fase.objects.create(
            modulo=self.modulo,
            titulo="Fase Preview",
            ordem=1,
        )

        self.questao = Questao.objects.create(
            fase=self.fase,
            enunciado="Questão disponível no preview",
        )

        self.opcao = Opcao.objects.create(
            questao=self.questao,
            texto="Resposta correta",
            e_correta=True,
        )

        self.client.login(
            username=self.professor.username,
            password="SenhaForte123!",
        )

    def test_professor_abre_sua_fase_diretamente(self):
        response = self.client.get(
            reverse(
                "fase_detalhe",
                args=[self.fase.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            'id="questoes-data"',
        )

        self.assertContains(
            response,
            "Resposta correta",
        )

    def test_preview_do_professor_reproduz_inicio_da_jornada_do_aluno(self):
        segunda = Fase.objects.create(
            modulo=self.modulo,
            titulo="Segunda fase",
            ordem=2,
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            ) + "?preview=aluno"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context["modo_preview_aluno"],
        )

        self.assertEqual(
            response.context["papel_exibicao"],
            "aluno",
        )

        modulos = response.context["modulos"]
        fases = list(
            modulos[0].fases.all()
        )

        self.assertEqual(
            modulos[0].status,
            "atual",
        )

        self.assertEqual(
            fases[0].status,
            "atual",
        )

        self.assertEqual(
            fases[1].status,
            "bloqueada",
        )

        self.assertContains(
            response,
            reverse(
                "fase_detalhe",
                args=[self.fase.id],
            ),
        )

        self.assertContains(
            response,
            "Pré-visualização como aluno",
        )

    def test_preview_do_professor_nao_marca_todas_as_fases_como_atuais(self):
        segunda = Fase.objects.create(
            modulo=self.modulo,
            titulo="Segunda fase",
            ordem=2,
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        modulos = response.context["modulos"]

        self.assertEqual(
            modulos[0].status,
            "professor",
        )

        fases = list(
            modulos[0].fases.all()
        )

        self.assertEqual(
            fases[0].status,
            "professor",
        )

        self.assertEqual(
            fases[1].status,
            "professor",
        )

        self.assertContains(
            response,
            'title="Abrir fase como professor"',
        )


class AcessoAlunoFaseTests(AutenticacaoBaseTests):
    def setUp(self):
        self.professor = self.criar_usuario(
            username="professor_fase",
        )

        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(
            update_fields=["tipo"]
        )

        self.aluno = self.criar_usuario(
            username="aluno_fase",
        )

        self.trilha = Disciplina.objects.create(
            nome="Trilha Fase",
            slug="trilha-fase",
            ativo=True,
            autor=self.professor,
        )

        self.modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Fase",
            ordem=1,
        )

        self.fase = Fase.objects.create(
            modulo=self.modulo,
            titulo="Fase Inicial",
            ordem=1,
        )

        Questao.objects.create(
            fase=self.fase,
            enunciado="Questão inicial",
        )

        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

    def test_aluno_enxerga_link_da_primeira_fase_no_mapa(self):
        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            reverse(
                "fase_detalhe",
                args=[self.fase.id],
            ),
        )

    def test_aluno_consegue_abrir_primeira_fase_da_trilha(self):
        response = self.client.get(
            reverse(
                "fase_detalhe",
                args=[self.fase.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )




class InterfaceVisualTests(AutenticacaoBaseTests):

    def setUp(self):
        self.professor = self.criar_usuario(
            username="professor_interface",
        )

        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(
            update_fields=["tipo"]
        )

        self.aluno = self.criar_usuario(
            username="aluno_interface",
        )

        self.trilha = Disciplina.objects.create(
            nome="Trilha Interface",
            slug="trilha-interface-testes",
            ativo=True,
            autor=self.professor,
        )

        self.modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Interface",
            ordem=1,
        )

        self.fase_1 = Fase.objects.create(
            modulo=self.modulo,
            titulo="Primeira fase",
            ordem=1,
        )

        self.fase_2 = Fase.objects.create(
            modulo=self.modulo,
            titulo="Segunda fase",
            ordem=2,
        )

        questao = Questao.objects.create(
            fase=self.fase_1,
            enunciado="Questao de interface",
        )

        Opcao.objects.create(
            questao=questao,
            texto="Resposta correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=questao,
            texto="Resposta incorreta",
            e_correta=False,
        )

    def test_editor_carrega_preview_com_multiplas_fases(self):
        self.client.login(
            username=self.professor.username,
            password="SenhaForte123!",
        )

        modulo_2 = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Segundo módulo",
            ordem=2,
        )

        Fase.objects.create(
            modulo=modulo_2,
            titulo="Fase do segundo módulo",
            ordem=1,
        )

        response = self.client.get(
            reverse(
                "editar_trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Primeira fase",
        )

        self.assertContains(
            response,
            "Segunda fase",
        )

        self.assertContains(
            response,
            "Fase do segundo módulo",
        )

        self.assertContains(
            response,
            reverse(
                "fase_detalhe",
                args=[self.fase_1.id],
            ),
        )

    def test_mapa_do_aluno_exibe_hud_e_controles(self):
        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            'id="controle-aparencia"',
        )

        self.assertContains(
            response,
            'id="seletor-tema-usuario"',
        )

        self.assertContains(
            response,
            "Nv.",
        )

        self.assertContains(
            response,
            str(self.aluno.perfil.moedas),
        )

        self.assertContains(
            response,
            str(self.aluno.perfil.vidas),
        )

    def test_fase_do_aluno_exibe_hud_e_dados_da_questao(self):
        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse(
                "fase_detalhe",
                args=[self.fase_1.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            'id="controle-aparencia"',
        )

        self.assertContains(
            response,
            'id="seletor-tema-usuario"',
        )

        self.assertContains(
            response,
            "Questao de interface",
        )

        self.assertContains(
            response,
            str(self.aluno.perfil.moedas),
        )

        self.assertContains(
            response,
            str(self.aluno.perfil.vidas),
        )

    def test_mapa_do_professor_usa_icone_play_vetorial(self):
        self.client.login(
            username=self.professor.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse(
                "trilha",
                args=[self.trilha.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            'title="Abrir fase como professor"',
        )

        self.assertContains(
            response,
            'viewBox="0 0 24 24"',
        )

        self.assertNotContains(
            response,
            ">▶<",
        )



class CatalogoMateriaTests(AutenticacaoBaseTests):

    def setUp(self):
        self.aluno = self.criar_usuario(
            username="aluno_catalogo",
        )

        self.professor = self.criar_usuario(
            username="professor_catalogo",
        )

        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(
            update_fields=["tipo"]
        )

        self.trilha = Disciplina.objects.create(
            nome="Jogo de Matemática",
            slug="jogo-matematica-catalogo",
            ativo=True,
            autor=self.professor,
            materia=Materia.objects.get(
                slug="matematica",
            ),
        )

        modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo de exemplo",
            ordem=1,
        )

        fase = Fase.objects.create(
            modulo=modulo,
            titulo="Fase de exemplo",
            ordem=1,
        )

        questao = Questao.objects.create(
            fase=fase,
            enunciado="Questão de catálogo",
        )

        Opcao.objects.create(
            questao=questao,
            texto="Correta",
            e_correta=True,
        )

        Opcao.objects.create(
            questao=questao,
            texto="Incorreta",
            e_correta=False,
        )

    def test_quatro_materias_do_catalogo_existentes(self):
        self.assertEqual(
            Materia.objects.filter(
                ativo=True,
            ).count(),
            4,
        )

        self.assertEqual(
            set(
                Materia.objects
                .filter(ativo=True)
                .values_list('slug', flat=True)
            ),
            {
                "matematica",
                "fisica",
                "geografia",
                "biologia",
            },
        )

    def test_aluno_abre_catalogo_de_materia_e_enxerga_jogo(self):
        self.client.login(
            username=self.aluno.username,
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse(
                "materia_detalhe",
                args=["matematica"],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Matemática",
        )

        self.assertContains(
            response,
            "Jogo de Matemática",
        )

        self.assertContains(
            response,
            reverse(
                "trilha",
                args=[self.trilha.id],
            ),
        )

    def test_aluno_nao_enxerga_jogo_em_rascunho_no_catalogo(self):
        Disciplina.objects.create(
            nome="Rascunho de Matemática",
            slug="rascunho-matematica-catalogo",
            ativo=False,
            autor=self.professor,
            materia=Materia.objects.get(
                slug="matematica",
            ),
        )

        self.client.login(
            username=self.aluno.username,
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
            "Rascunho de Matemática",
        )

    def test_catalogo_json_distribui_respostas_corretas_por_posicao(self):
        caminho_catalogo = (
            Path(__file__).resolve().parent.parent
            / "dados_catalogo_ensino_medio.json"
        )

        with caminho_catalogo.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        for materia in dados["materias"]:
            for jogo in materia["jogos"]:
                for modulo in jogo["modulos"]:
                    for fase in modulo["fases"]:
                        posicoes = [
                            next(
                                indice
                                for indice, opcao in enumerate(
                                    questao["opcoes"],
                                    start=1,
                                )
                                if opcao["correta"]
                            )
                            for questao in fase["questoes"]
                        ]

                        self.assertEqual(
                            len(posicoes),
                            4,
                            msg=(
                                "Cada fase do catálogo deve possuir "
                                "exatamente 4 questões."
                            ),
                        )

                        self.assertEqual(
                            sorted(posicoes),
                            [1, 2, 3, 4],
                            msg=(
                                "Respostas corretas precisam ocupar "
                                "as quatro posições em cada fase."
                            ),
                        )

    def test_catalogo_json_possui_quatro_modulos_doze_fases_e_quarenta_e_oito_questoes_por_jogo(self):
        caminho_catalogo = (
            Path(__file__).resolve().parent.parent
            / "dados_catalogo_ensino_medio.json"
        )

        with caminho_catalogo.open(
            "r",
            encoding="utf-8",
        ) as arquivo:
            dados = json.load(arquivo)

        total_jogos = 0
        total_modulos = 0
        total_fases = 0
        total_questoes = 0

        for materia in dados["materias"]:
            for jogo in materia["jogos"]:
                total_jogos += 1

                self.assertEqual(
                    len(jogo["modulos"]),
                    4,
                    msg=f'{jogo["slug"]} deve possuir 4 módulos.',
                )

                questoes_jogo = 0

                for modulo in jogo["modulos"]:
                    self.assertEqual(
                        len(modulo["fases"]),
                        3,
                        msg=(
                            f'{jogo["slug"]} · módulo {modulo["ordem"]} '
                            "deve possuir 3 fases."
                        ),
                    )

                    total_modulos += 1
                    total_fases += len(modulo["fases"])

                    for fase in modulo["fases"]:
                        self.assertEqual(
                            len(fase["questoes"]),
                            4,
                            msg=(
                                f'{jogo["slug"]} · módulo {modulo["ordem"]} '
                                "deve possuir 4 questões."
                            ),
                        )

                        questoes_jogo += len(fase["questoes"])
                        total_questoes += len(fase["questoes"])

                self.assertEqual(
                    questoes_jogo,
                    48,
                    msg=f'{jogo["slug"]} deve possuir 48 questões.',
                )

        self.assertEqual(total_jogos, 12)
        self.assertEqual(total_modulos, 48)
        self.assertEqual(total_fases, 144)
        self.assertEqual(total_questoes, 576)


    def test_professor_cria_jogo_associado_a_materia(self):
        self.client.login(
            username=self.professor.username,
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("criar_trilha"),
            {
                "materia": Materia.objects.get(
                    slug="fisica",
                ).id,
                "nome": "Novo Jogo de Física",
                "slug": "novo-jogo-fisica",
                "descricao": "Jogo de teste.",
                "tema": "tema-oceano",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard_professor"),
        )

        jogo = Disciplina.objects.get(
            slug="novo-jogo-fisica",
        )

        self.assertEqual(
            jogo.materia.slug,
            "fisica",
        )

        self.assertFalse(
            jogo.ativo,
        )
