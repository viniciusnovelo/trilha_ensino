import asyncio
import os
import re
from contextlib import asynccontextmanager

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from asgiref.sync import sync_to_async
from playwright.async_api import expect, async_playwright

from .models import Disciplina, Fase, Modulo, Opcao, Questao


class EditorBrowserTests(StaticLiveServerTestCase):
    """Regressão de navegador para os fluxos críticos do editor de trilhas.

    Os métodos de teste são assíncronos porque a API assíncrona do Playwright
    não cria um event loop adicional dentro de um teste síncrono do Django.
    Isso mantém o ORM síncrono fora de um contexto assíncrono e evita
    SynchronousOnlyOperation no runner do Django.
    """

    def setUp(self):
        self.professor = User.objects.create_user(
            username="professor_browser",
            password="SenhaForte123!",
        )
        self.professor.perfil.tipo = "professor"
        self.professor.perfil.save(update_fields=["tipo"])

        self.trilha = Disciplina.objects.create(
            nome="Trilha Browser",
            slug="trilha-browser",
            ativo=False,
            autor=self.professor,
        )
        self.modulo = Modulo.objects.create(
            disciplina=self.trilha,
            titulo="Módulo Browser",
            descricao="Descrição inicial do módulo.",
            ordem=1,
        )
        self.fase = Fase.objects.create(
            modulo=self.modulo,
            titulo="Fase Browser",
            ordem=1,
            tipo="quiz",
            xp_recompensa=50,
            moedas_recompensa=10,
            deslocamento_y=0,
        )
        self.questao = Questao.objects.create(
            fase=self.fase,
            enunciado="Enunciado inicial da questão.",
            explicacao_erro="Feedback inicial.",
        )
        for ordem, texto, correta in [
            (1, "Alternativa A", True),
            (2, "Alternativa B", False),
            (3, "Alternativa C", False),
            (4, "Alternativa D", False),
        ]:
            Opcao.objects.create(
                questao=self.questao,
                texto=texto,
                e_correta=correta,
                ordem=ordem,
            )

        self.editor_url = (
            f"{self.live_server_url}"
            f"{reverse('editar_trilha', args=[self.trilha.id])}"
        )

    @asynccontextmanager
    async def _browser_page(self):
        headless = os.getenv("PLAYWRIGHT_HEADLESS", "1").lower() not in {
            "0",
            "false",
            "no",
        }
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 1000},
            )
            page = await context.new_page()
            page_errors = []

            def handle_page_error(error):
                page_errors.append(str(error))

            page.on("pageerror", handle_page_error)

            def handle_console(message):
                if message.type == "log" and message.text.startswith("EDITOR_SELECTION") or message.text.startswith("EDITOR_MATCH_COUNT"):
                    page_errors.append("CONSOLE:" + message.text)

            page.on("console", handle_console)
            try:
                yield page, page_errors
            finally:
                await context.close()
                await browser.close()

    async def _login_and_open_editor(self, page):
        login_url = f"{self.live_server_url}{reverse('login')}"
        await page.goto(login_url)
        await page.get_by_label("Usuário").fill(self.professor.username)
        await page.get_by_label("Senha").fill("SenhaForte123!")
        await page.get_by_role("button", name="Entrar").click()

        await expect(page).to_have_url(re.compile(r"/estudio/?$"))
        await page.goto(self.editor_url)
        await expect(page).to_have_url(self.editor_url)
        await expect(
            page.get_by_role("heading", name=self.trilha.nome)
        ).to_be_visible()

    def _assert_no_page_errors(self, page_errors):
        self.assertEqual(
            page_errors,
            [],
            msg=f"Erros JavaScript no navegador: {page_errors}",
        )

    def _content_item(self, page, item_type, item_id):
        return page.locator(
            f'[data-editor-select="{item_type}"]'
            f'[data-editor-id="{item_id}"]'
        ).first

    async def _select_content_item(self, page, item_type, item_id, label):
        item = self._content_item(page, item_type, item_id)
        hierarchy_opened = False

        if item_type == "fase":
            if await self._module_content(page).get_attribute("hidden") is not None:
                await self._module_toggle(page).click()
                hierarchy_opened = True
        elif item_type == "questao":
            if await self._module_content(page).get_attribute("hidden") is not None:
                await self._module_toggle(page).click()
                hierarchy_opened = True
            if await self._phase_content(page).get_attribute("hidden") is not None:
                await self._phase_toggle(page).click()
                hierarchy_opened = True

        if hierarchy_opened:
            await expect(self._module_content(page)).not_to_have_attribute("hidden", "")
            if item_type == "questao":
                await expect(self._phase_content(page)).not_to_have_attribute("hidden", "")

        selection_target = page.locator(
            f'[data-editor-select="{item_type}"]'
            f'[data-editor-id="{item_id}"].editor-selection-target'
        ).first
        await expect(selection_target).to_be_visible()
        await selection_target.click()
        return item

    def _module_toggle(self, page):
        return page.locator(
            f'[data-editor-toggle="modulo"][data-modulo-id="{self.modulo.id}"]'
        )

    def _module_content(self, page):
        return page.locator(f"#editor-module-content-{self.modulo.id}")

    def _phase_toggle(self, page):
        return page.locator(
            f'[data-editor-toggle="fase"][data-fase-id="{self.fase.id}"]'
        )

    def _phase_content(self, page):
        return page.locator(f"#editor-phase-content-{self.fase.id}")

    def _map_phase_button(self, page):
        return page.locator(
            f'.fase-node[data-id="{self.fase.id}"]'
            ' button[data-editor-select="fase"]'
        )

    def _map_phase_circle(self, page):
        return page.locator(
            f'.fase-node[data-id="{self.fase.id}"] .editor-fase-circle'
        )

    async def test_professor_autenticado_abre_editor_da_trilha_isolada(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            await expect(page).to_have_url(self.editor_url)
            await expect(
                page.get_by_text("Estrutura do jogo", exact=True)
            ).to_be_visible()

        self._assert_no_page_errors(page_errors)

    async def test_selecao_de_modulo_fase_e_questao_atualiza_detalhes(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            modulo = await self._select_content_item(
                page, "modulo", self.modulo.id, self.modulo.titulo
            )
            await expect(modulo).to_contain_class("editor-selected")
            await expect(
                page.locator(
                    f'[data-editor-select="modulo"][data-editor-id="{self.modulo.id}"]'
                ).nth(1)
            ).to_contain_class("editor-selected")
            await expect(self._module_content(page)).to_be_visible()
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.modulo.titulo)

            await self._phase_toggle(page).click()
            fase = await self._select_content_item(
                page, "fase", self.fase.id, self.fase.titulo
            )
            await expect(fase).to_contain_class("editor-selected")
            await expect(self._phase_content(page)).to_be_visible()
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.fase.titulo)

            # Recolher antes de selecionar a questão garante que o teste
            # valide também a expansão automática da fase correspondente.
            await self._phase_toggle(page).click()
            await expect(self._phase_content(page)).to_be_hidden()

            questao = await self._select_content_item(
                page, "questao", self.questao.id, self.questao.enunciado
            )
            await expect(questao).to_contain_class("editor-selected")
            await expect(self._phase_content(page)).to_be_visible()
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.questao.enunciado)

        self._assert_no_page_errors(page_errors)

    async def test_modulo_e_fase_podem_expandir_e_recolher_independentemente(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            await expect(self._module_content(page)).to_be_hidden()
            await expect(self._phase_content(page)).to_be_hidden()

            await self._module_toggle(page).click()
            await expect(self._module_content(page)).to_be_visible()
            await expect(self._module_toggle(page)).to_have_attribute(
                "aria-expanded", "true"
            )

            await self._phase_toggle(page).click()
            await expect(self._phase_content(page)).to_be_visible()
            await expect(self._phase_toggle(page)).to_have_attribute(
                "aria-expanded", "true"
            )

            await self._phase_toggle(page).click()
            await expect(self._phase_content(page)).to_be_hidden()

            await self._module_toggle(page).click()
            await expect(self._module_content(page)).to_be_hidden()
            await expect(self._module_toggle(page)).to_have_attribute(
                "aria-expanded", "false"
            )

        self._assert_no_page_errors(page_errors)

    async def test_selecionar_fase_no_mapa_abre_sua_hierarquia(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            await self._module_toggle(page).click()
            await expect(self._phase_content(page)).to_be_hidden()

            await self._map_phase_button(page).click()

            await expect(self._module_content(page)).to_be_visible()
            await expect(self._phase_content(page)).to_be_visible()
            await expect(
                self._phase_toggle(page)
            ).to_have_attribute("aria-expanded", "true")
            await expect(
                page.locator(
                    f'[data-editor-select="fase"][data-editor-id="{self.fase.id}"]'
                ).first
            ).to_contain_class("editor-selected")

        self._assert_no_page_errors(page_errors)

    async def test_painel_detalhes_abre_fecha_e_libera_espaco_para_o_mapa(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            workspace = page.locator(".editor-workspace")
            details = page.locator("#editor-details-panel")
            map_panel = page.locator("#editor-map-panel")

            await expect(details).to_be_hidden()
            await expect(workspace).to_have_class(re.compile(r"details-collapsed"))

            await self._select_content_item(
                page, "modulo", self.modulo.id, self.modulo.titulo
            )
            await expect(details).to_be_visible()
            await expect(workspace).to_have_class(re.compile(r"details-open"))

            map_open_width = (await map_panel.bounding_box())["width"]

            await page.get_by_role(
                "button", name="Recolher detalhes"
            ).click()
            await expect(details).to_be_hidden()
            await expect(workspace).to_have_class(
                re.compile(r"details-collapsed")
            )
            await expect(
                self._content_item(page, "modulo", self.modulo.id)
            ).to_contain_class("editor-selected")

            map_closed_width = (await map_panel.bounding_box())["width"]
            self.assertGreater(
                map_closed_width,
                map_open_width,
                "O mapa deve ganhar espaço quando Detalhes estiver recolhido.",
            )

            await self._select_content_item(
                page, "fase", self.fase.id, self.fase.titulo
            )
            await expect(details).to_be_visible()
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.fase.titulo)

        self._assert_no_page_errors(page_errors)

    async def test_selecao_de_modulo_no_mapa_sincroniza_conteudo_e_detalhes(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            url_antes = page.url
            map_module = page.locator(
                f'[data-editor-select="modulo"][data-editor-id="{self.modulo.id}"]'
            ).last.locator(".editor-module-number")
            await expect(map_module).to_be_visible()
            await map_module.click()

            await expect(page).to_have_url(url_antes)
            await expect(
                self._content_item(page, "modulo", self.modulo.id)
            ).to_contain_class("editor-selected")
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.modulo.titulo)
            await expect(self._module_content(page)).to_be_visible()

        self._assert_no_page_errors(page_errors)

    async def test_selecao_cruzada_da_fase_entre_conteudo_mapa_e_detalhes(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            fase_conteudo = await self._select_content_item(
                page, "fase", self.fase.id, self.fase.titulo
            )
            await expect(self._map_phase_circle(page)).to_contain_class(
                "editor-selected"
            )

            url_antes = page.url
            await self._map_phase_button(page).click()

            await expect(page).to_have_url(url_antes)
            await expect(fase_conteudo).to_contain_class("editor-selected")
            await expect(
                page.locator("#editor-details-content")
            ).to_contain_text(self.fase.titulo)

            abrir_fase = page.get_by_role("link", name="Abrir fase")
            await expect(abrir_fase).to_be_visible()
            await abrir_fase.click()
            await expect(page).to_have_url(
                f"{self.live_server_url}"
                f"{reverse('fase_detalhe', args=[self.fase.id])}"
            )

        self._assert_no_page_errors(page_errors)

    async def test_modal_de_modulo_fica_visivel_e_persiste_edicao(self):
        novo_titulo = "Módulo Browser Editado"

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)
            details = page.locator("#editor-details-content")
            await self._select_content_item(
                page, "modulo", self.modulo.id, self.modulo.titulo
            )
            await details.get_by_role(
                "button", name="Editar módulo"
            ).click()

            modal = page.locator("#modal-editar-modulo")
            await expect(modal).to_be_visible()
            await expect(
                page.locator("#editar-modulo-titulo")
            ).to_have_value(self.modulo.titulo)
            await expect(
                page.locator("#editar-modulo-descricao")
            ).to_have_value(self.modulo.descricao)
            await expect(
                page.locator("#editar-modulo-ordem")
            ).to_have_value(str(self.modulo.ordem))

            await page.locator("#editar-modulo-titulo").fill(novo_titulo)

            async with page.expect_response(
                lambda response: (
                    response.request.method == "POST"
                    and (
                        f"/estudio/ajax/modulo/{self.modulo.id}/editar/"
                        in response.url
                    )
                    and response.ok
                )
            ):
                await modal.get_by_role(
                    "button", name="Salvar alterações"
                ).click()

            await expect(modal).to_be_hidden()
            await expect(
                page.get_by_text(novo_titulo, exact=True).first
            ).to_be_visible()

            await page.reload()
            await expect(
                page.get_by_text(novo_titulo, exact=True).first
            ).to_be_visible()

        await self.modulo.arefresh_from_db()
        self.assertEqual(self.modulo.titulo, novo_titulo)
        self._assert_no_page_errors(page_errors)

    async def test_modal_de_fase_fica_visivel_e_persiste_edicao(self):
        novo_titulo = "Fase Browser Editada"

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)
            details = page.locator("#editor-details-content")
            await self._select_content_item(
                page, "fase", self.fase.id, self.fase.titulo
            )
            await details.get_by_role(
                "button", name="Editar fase"
            ).click()

            modal = page.locator("#modal-editar-fase")
            await expect(modal).to_be_visible()
            await expect(
                page.locator("#editar-fase-titulo")
            ).to_have_value(self.fase.titulo)
            await expect(
                page.locator("#editar-fase-ordem")
            ).to_have_value(str(self.fase.ordem)
            )
            await expect(
                page.locator("#editar-fase-tipo")
            ).to_have_value(self.fase.tipo)

            await page.locator("#editar-fase-titulo").fill(novo_titulo)

            async with page.expect_response(
                lambda response: (
                    response.request.method == "POST"
                    and (
                        f"/estudio/ajax/fase/{self.fase.id}/editar/"
                        in response.url
                    )
                    and response.ok
                )
            ):
                await modal.get_by_role(
                    "button", name="Salvar alterações"
                ).click()

            await expect(modal).to_be_hidden()
            await expect(
                page.get_by_text(novo_titulo, exact=True).first
            ).to_be_visible()

            await page.reload()
            await expect(
                page.get_by_text(novo_titulo, exact=True).first
            ).to_be_visible()

        await self.fase.arefresh_from_db()
        self.assertEqual(self.fase.titulo, novo_titulo)
        self._assert_no_page_errors(page_errors)

    async def test_modal_de_questao_fica_visivel_e_persiste_edicao(self):
        novo_enunciado = "Enunciado Browser Editado."

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)
            details = page.locator("#editor-details-content")
            await self._select_content_item(
                page, "questao", self.questao.id, self.questao.enunciado
            )
            await details.get_by_role(
                "button", name="Editar questão"
            ).click()

            modal = page.locator("#modal-editar-questao")
            await expect(modal).to_be_visible()
            await expect(
                page.locator("#editar-questao-enunciado")
            ).to_have_value(self.questao.enunciado)
            await expect(
                page.locator("#editar-questao-op-0")
            ).to_have_value("Alternativa A")
            await expect(
                page.locator(
                    '#form-editar-questao '
                    'input[name="op_correta"][value="0"]'
                )
            ).to_be_checked()

            await page.locator(
                "#editar-questao-enunciado"
            ).fill(novo_enunciado)

            async with page.expect_response(
                lambda response: (
                    response.request.method == "POST"
                    and (
                        f"/estudio/ajax/questao/{self.questao.id}/editar/"
                        in response.url
                    )
                    and response.ok
                )
            ):
                await modal.get_by_role(
                    "button", name="Salvar alterações"
                ).click()

            await expect(modal).to_be_hidden()
            await expect(
                page.get_by_text(novo_enunciado, exact=True).first
            ).to_be_visible()

            await page.reload()
            await expect(
                page.get_by_text(novo_enunciado, exact=True).first
            ).to_be_visible()

        await self.questao.arefresh_from_db()
        self.assertEqual(self.questao.enunciado, novo_enunciado)
        self._assert_no_page_errors(page_errors)

    async def test_exclusao_de_questao_exige_confirmacao_e_remove_registro(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)
            await self._module_toggle(page).click()
            await self._phase_toggle(page).click()

            page.once("dialog", lambda dialog: dialog.accept())
            delete_button = page.locator(
                f'[data-editor-action="excluir-questao"]'
                f'[data-questao-id="{self.questao.id}"]'
            )
            await delete_button.click()

            await expect(
                page.locator(f"#questao-card-{self.questao.id}")
            ).to_be_hidden()

        self.assertFalse(
            await Questao.objects.filter(id=self.questao.id).aexists()
        )
        self._assert_no_page_errors(page_errors)

    async def test_trajetoria_dinamica_conecta_as_12_fases_em_sequencia_global(self):
        for fase_ordem in (2, 3):
            await sync_to_async(Fase.objects.create)(
                modulo=self.modulo,
                titulo=f"Fase 1.{fase_ordem}",
                ordem=fase_ordem,
                tipo="quiz",
                xp_recompensa=50,
                moedas_recompensa=10,
                deslocamento_y=0,
            )

        for modulo_ordem in range(2, 5):
            modulo = await sync_to_async(Modulo.objects.create)(
                disciplina=self.trilha,
                titulo=f"Módulo Browser {modulo_ordem}",
                ordem=modulo_ordem,
            )
            for fase_ordem in range(1, 4):
                await sync_to_async(Fase.objects.create)(
                    modulo=modulo,
                    titulo=f"Fase {modulo_ordem}.{fase_ordem}",
                    ordem=fase_ordem,
                    tipo="quiz",
                    xp_recompensa=50,
                    moedas_recompensa=10,
                    deslocamento_y=0,
                )

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            nodes = page.locator(".fase-node[data-index]")
            connectors = page.locator(".editor-connector[data-connector-index]")
            await expect(nodes).to_have_count(12)
            await expect(connectors).to_have_count(11)

            for index in range(11):
                source = nodes.nth(index)
                target = nodes.nth(index + 1)
                connector = page.locator(
                    f'.editor-connector[data-connector-index="{index}"] .linha-conector'
                )
                await expect(connector).to_have_attribute("d", re.compile(r"^M 0,"))
                self.assertNotEqual(await connector.get_attribute("d"), "")

                source_index = await source.get_attribute("data-index")
                target_index = await target.get_attribute("data-index")
                self.assertEqual(int(target_index), int(source_index) + 1)

                if index in {2, 5, 8}:
                    self.assertNotEqual(
                        await source.get_attribute("data-modulo-id"),
                        await target.get_attribute("data-modulo-id"),
                        f"A transição global {index} deve atravessar módulos.",
                    )

            auto_positions = [
                int(float(await nodes.nth(index).get_attribute("data-auto-y")))
                for index in range(12)
            ]
            self.assertGreater(
                len(set(auto_positions)),
                2,
                "A trajetória não deve repetir apenas uma onda periódica fixa.",
            )

        self._assert_no_page_errors(page_errors)

    async def test_geometria_global_tem_contratos_de_continuidade(self):
        for modulo_ordem in range(2, 5):
            modulo = await sync_to_async(Modulo.objects.create)(
                disciplina=self.trilha,
                titulo=f"Módulo Browser {modulo_ordem}",
                ordem=modulo_ordem,
            )
            for fase_ordem in range(1, 4):
                await sync_to_async(Fase.objects.create)(
                    modulo=modulo,
                    titulo=f"Fase {modulo_ordem}.{fase_ordem}",
                    ordem=fase_ordem,
                    tipo="quiz",
                    xp_recompensa=50,
                    moedas_recompensa=10,
                    deslocamento_y=0,
                )

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            nodes = page.locator(".fase-node[data-index]")
            connectors = page.locator(".editor-connector[data-connector-index]")

            await expect(nodes).to_have_count(12)
            await expect(connectors).to_have_count(11)

            ys = [
                float(await nodes.nth(index).get_attribute("data-render-y"))
                for index in range(12)
            ]

            self.assertGreaterEqual(
                len({round(value, 1) for value in ys}),
                3,
                "A trajetória precisa ter pelo menos três alturas visuais distintas.",
            )

            for index in range(11):
                source = nodes.nth(index)
                target = nodes.nth(index + 1)
                connector = page.locator(
                    f'.editor-connector[data-connector-index="{index}"] .linha-conector'
                )

                self.assertEqual(
                    int(await target.get_attribute("data-index")),
                    int(await source.get_attribute("data-index")) + 1,
                )
                path = await connector.get_attribute("d")
                self.assertRegex(path or "", r"^M 0,-?\d+(?:\.\d+)? C ")
                self.assertNotEqual(path, "")

                self.assertNotEqual(
                    round(ys[index], 1),
                    round(ys[index + 1], 1),
                    f"F{index + 1} e F{index + 2} não devem compartilhar a mesma altura.",
                )

                values = re.findall(r"-?\d+(?:\.\d+)?", path or "")
                self.assertGreaterEqual(len(values), 6)
                control_xs = [float(values[2]), float(values[4])]
                self.assertGreaterEqual(control_xs[0], 0)
                self.assertLessEqual(control_xs[1], 100)
                self.assertLessEqual(control_xs[0], control_xs[1])

            for index in (2, 5, 8):
                source = nodes.nth(index)
                target = nodes.nth(index + 1)
                self.assertNotEqual(
                    await source.get_attribute("data-modulo-id"),
                    await target.get_attribute("data-modulo-id"),
                    f"A transição F{index + 1} → F{index + 2} deve cruzar módulos.",
                )

        self._assert_no_page_errors(page_errors)

    async def test_jornada_global_mantem_conector_entre_modulos(self):
        modulo2 = await sync_to_async(Modulo.objects.create)(
            disciplina=self.trilha,
            titulo="Módulo Browser 2",
            descricao="Segundo módulo.",
            ordem=2,
        )
        fase2 = await sync_to_async(Fase.objects.create)(
            modulo=modulo2,
            titulo="Fase Browser 2",
            ordem=1,
            tipo="quiz",
            xp_recompensa=50,
            moedas_recompensa=10,
            deslocamento_y=24,
        )
        modulo3 = await sync_to_async(Modulo.objects.create)(
            disciplina=self.trilha,
            titulo="Módulo Browser 3",
            descricao="Terceiro módulo.",
            ordem=3,
        )
        await sync_to_async(Fase.objects.create)(
            modulo=modulo3,
            titulo="Fase Browser 3",
            ordem=1,
            tipo="quiz",
            xp_recompensa=50,
            moedas_recompensa=10,
            deslocamento_y=-18,
        )

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            nodes = page.locator(".fase-node[data-index]")
            connectors = page.locator(".editor-connector[data-connector-index]")
            await expect(nodes).to_have_count(3)
            await expect(connectors).to_have_count(2)

            first = nodes.nth(0)
            second = nodes.nth(1)
            self.assertNotEqual(
                await first.get_attribute("data-modulo-id"),
                await second.get_attribute("data-modulo-id"),
            )

            for index in range(2):
                path = page.locator(
                    f'.editor-connector[data-connector-index="{index}"] .linha-conector'
                )
                await expect(path).to_have_attribute("d", re.compile(r"^M 0,"))
                self.assertNotEqual(await path.get_attribute("d"), "")

            path_before = await page.locator(
                '.editor-connector[data-connector-index="0"] .linha-conector'
            ).get_attribute("d")

            await self._map_phase_button(page).click()
            await page.get_by_title("Aumentar zoom").click()

            path_after_zoom = await page.locator(
                '.editor-connector[data-connector-index="0"] .linha-conector'
            ).get_attribute("d")
            self.assertEqual(path_before, path_after_zoom)

            await page.get_by_title("Diminuir zoom").click()
            await expect(
                page.locator(
                    '.editor-connector[data-connector-index="0"] .linha-conector'
                )
            ).to_have_attribute("d", path_before)

        self._assert_no_page_errors(page_errors)

    async def test_arraste_recalcula_conectores_com_y_automatico_e_persistido(self):
        modulo2 = await sync_to_async(Modulo.objects.create)(
            disciplina=self.trilha,
            titulo="Módulo Browser 2",
            ordem=2,
        )
        await sync_to_async(Fase.objects.create)(
            modulo=modulo2,
            titulo="Fase Browser 2",
            ordem=1,
            tipo="quiz",
            deslocamento_y=0,
        )

        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            path_before = await page.locator(
                '.editor-connector[data-connector-index="0"] .linha-conector'
            ).get_attribute("d")

            handle = page.locator(
                f'.fase-node[data-id="{self.fase.id}"] .drag-handle'
            )
            await handle.scroll_into_view_if_needed()
            box = await handle.bounding_box()
            self.assertIsNotNone(box)

            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(start_x, start_y + 45, steps=5)
            await page.mouse.up()

            path_after = await page.locator(
                '.editor-connector[data-connector-index="0"] .linha-conector'
            ).get_attribute("d")
            self.assertNotEqual(path_before, path_after)

            node = page.locator(f'.fase-node[data-id="{self.fase.id}"]')
            custom_y = int(float(await node.get_attribute("data-y")))
            auto_y = int(float(await node.get_attribute("data-auto-y")))
            render_y = int(float(await node.get_attribute("data-render-y")))
            self.assertEqual(render_y, custom_y + auto_y)

            await page.reload()
            node = page.locator(f'.fase-node[data-id="{self.fase.id}"]')
            await expect(node).to_have_attribute("data-y", str(custom_y))
            self.assertEqual(
                int(float(await node.get_attribute("data-render-y"))),
                custom_y + int(float(await node.get_attribute("data-auto-y"))),
            )

        await self.fase.arefresh_from_db()
        self.assertEqual(self.fase.deslocamento_y, custom_y)
        self._assert_no_page_errors(page_errors)

    async def test_controles_do_mapa_e_arraste_de_fase_funcionam_e_persistem(self):
        async with self._browser_page() as (page, page_errors):
            await self._login_and_open_editor(page)

            zoom = page.locator("#map-zoom-value")
            await expect(zoom).to_have_text("100%")

            zoom_out = page.get_by_title("Diminuir zoom")
            await expect(zoom_out).to_be_visible()
            await zoom_out.click()
            await expect(zoom).to_have_text("90%")

            zoom_in = page.get_by_title("Aumentar zoom")
            await expect(zoom_in).to_be_visible()
            await zoom_in.click()
            await expect(zoom).to_have_text("100%")

            await page.get_by_role(
                "button", name="Ajustar"
            ).click()
            await expect(zoom).to_have_text(re.compile(r"^\d+%$"))

            handle = page.locator(
                f'.fase-node[data-id="{self.fase.id}"] .drag-handle'
            )
            await handle.scroll_into_view_if_needed()
            box = await handle.bounding_box()
            self.assertIsNotNone(box)

            old_y = self.fase.deslocamento_y
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2

            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(
                start_x, start_y + 50, steps=5
            )

            novo_y_durante_arraste = int(
                float(
                    await page.locator(
                        f'.fase-node[data-id="{self.fase.id}"]'
                    ).get_attribute("data-y")
                )
            )
            self.assertNotEqual(novo_y_durante_arraste, old_y)

            await page.mouse.up()

            novo_y = int(
                float(
                    await page.locator(
                        f'.fase-node[data-id="{self.fase.id}"]'
                    ).get_attribute("data-y")
                )
            )
            self.assertNotEqual(novo_y, old_y)

            for _ in range(20):
                await self.fase.arefresh_from_db()
                if self.fase.deslocamento_y == novo_y:
                    break
                await asyncio.sleep(0.25)

            self.assertEqual(self.fase.deslocamento_y, novo_y)

            await page.reload()
            await expect(
                page.locator(
                    f'.fase-node[data-id="{self.fase.id}"]'
                )
            ).to_have_attribute("data-y", str(novo_y))

        await self.fase.arefresh_from_db()
        self.assertEqual(self.fase.deslocamento_y, novo_y)
        self._assert_no_page_errors(page_errors)
