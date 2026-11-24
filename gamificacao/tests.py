import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class GamificacaoTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="aluno",
            password="SenhaForte123!",
        )

    def test_perfil_expoe_calculos_de_xp(self):
        perfil = self.usuario.perfil

        self.assertEqual(perfil.nivel, 1)
        self.assertEqual(perfil.xp_no_nivel, 0)
        self.assertEqual(perfil.xp_proximo_nivel, 200)
        self.assertEqual(perfil.xp_faltante, 200)
        self.assertEqual(perfil.progresso_nivel, 0)

        perfil.xp_total = 250
        perfil.save(
            update_fields=["xp_total"]
        )

        self.assertEqual(perfil.nivel, 2)
        self.assertEqual(perfil.xp_no_nivel, 50)
        self.assertEqual(perfil.xp_proximo_nivel, 400)
        self.assertEqual(perfil.xp_faltante, 150)
        self.assertEqual(perfil.progresso_nivel, 25)

    def test_aluno_pode_trocar_tema_e_persistir(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("atualizar_tema_usuario"),
            data=json.dumps({
                "tema": "tema-floresta"
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.usuario.refresh_from_db()

        self.assertEqual(
            self.usuario.perfil.tema_fundo,
            "tema-floresta",
        )

    def test_aluno_pode_trocar_aparencia_e_persistir(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("atualizar_aparencia_usuario"),
            data=json.dumps({
                "aparencia": "escuro",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        self.usuario.refresh_from_db()

        self.assertEqual(
            self.usuario.perfil.aparencia_interface,
            "escuro",
        )

    def test_aparencia_invalida_e_rejeitada(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("atualizar_aparencia_usuario"),
            data=json.dumps({
                "aparencia": "inexistente",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_novos_temas_de_paisagem_sao_validos(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        for tema in ("tema-aurora", "tema-oceano"):
            response = self.client.post(
                reverse("atualizar_tema_usuario"),
                data=json.dumps({"tema": tema}),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)
            self.usuario.refresh_from_db()
            self.assertEqual(
                self.usuario.perfil.tema_fundo,
                tema,
            )


    def test_tema_invalido_e_rejeitado(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        response = self.client.post(
            reverse("atualizar_tema_usuario"),
            data=json.dumps({
                "tema": "tema-inexistente"
            }),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_loja_exibe_apenas_itens_de_vida(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        response = self.client.get(
            reverse("loja")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Recarga completa de vidas",
        )

    def test_compra_de_vida_atualiza_saldo_e_vidas(self):
        self.client.login(
            username="aluno",
            password="SenhaForte123!",
        )

        self.usuario.perfil.moedas = 50
        self.usuario.perfil.vidas = 3
        self.usuario.perfil.save(
            update_fields=["moedas", "vidas"]
        )

        self.client.get(
            reverse("loja")
        )

        from gamificacao.models import ItemLoja

        item = ItemLoja.objects.get(
            nome="Recarga econômica de vidas"
        )

        response = self.client.post(
            reverse(
                "comprar_item",
                args=[item.id],
            )
        )

        self.assertRedirects(
            response,
            reverse("loja"),
        )

        self.usuario.refresh_from_db()

        self.assertEqual(
            self.usuario.perfil.moedas,
            32,
        )

        self.assertEqual(
            self.usuario.perfil.vidas,
            5,
        )
