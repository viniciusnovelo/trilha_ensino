"""Fluxo crítico de player com Playwright, seguindo o runner browser_tests.py do projeto."""
import os
from contextlib import asynccontextmanager
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from playwright.async_api import async_playwright, expect
from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao


class PhysicsPlayerBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aluno_fisica_browser', password='SenhaForte123!')
        self.materia = Materia.objects.create(nome='Física', slug='fisica-browser')
        self.disciplina = Disciplina.objects.create(nome='Física', slug='fisica-browser', materia=self.materia, ativo=True)
        self.modulo = Modulo.objects.create(disciplina=self.disciplina, titulo='Módulo 1', ordem=1)
        self.fase = Fase.objects.create(modulo=self.modulo, titulo='Cinemática', ordem=1)

    @asynccontextmanager
    async def browser_page(self):
        headless = os.getenv('PLAYWRIGHT_HEADLESS', '1').lower() not in {'0', 'false', 'no'}
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page(viewport={'width': 1365, 'height': 900})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            try:
                yield page, errors
            finally:
                await browser.close()

    async def login(self, page):
        await page.goto(self.live_server_url + reverse('login'))
        await page.get_by_label('Usuário').fill(self.user.username)
        await page.get_by_label('Senha').fill('SenhaForte123!')
        await page.get_by_role('button', name='Entrar').click()

    def numeric_data(self):
        return {
            'title': 'MRU interativo', 'topic': 'MRU', 'context': 'Carrinho em uma pista reta.',
            'simulation': {'scene': 'mru_track', 'description': 'Pista com carrinho.', 'show_vectors': True, 'show_live_readouts': True,
                           'parameters': [{'key':'v','label':'Velocidade','value':2,'unit':'m/s','min':0,'max':10,'step':1,'hint':''},
                                          {'key':'t','label':'Tempo','value':3,'unit':'s','min':0,'max':10,'step':1,'hint':''},
                                          {'key':'x0','label':'Posição inicial','value':1,'unit':'m','min':0,'max':10,'step':1,'hint':''}]},
            'challenge': {'prompt':'Qual é a posição final?', 'answer': {'type':'numeric','formula':'mru_position','unit':'m','tolerance':0.02,'digits':2,'display_scale':1,'display_unit':'m'}, 'hint':'Use x=x0+vt.', 'solution':'Some a posição inicial ao deslocamento.'},
            'completion': {'xp':30,'mastery_tag':'MRU'},
        }

    async def test_numeric_player_parameter_slider_answer_and_finish(self):
        data = self.numeric_data()
        Questao.objects.create(fase=self.fase, enunciado=data['challenge']['prompt'], tipo_resposta='numeric', codigo_fonte='browser-numeric', dados_dinamicos=data)
        async with self.browser_page() as (page, errors):
            await self.login(page)
            await page.goto(self.live_server_url + reverse('physics_player', args=[self.fase.id]))
            await expect(page.locator('#simulation')).to_be_visible()
            await expect(page.locator('#parameters input[type=range]')).to_have_count(3)
            await page.locator('#numeric-value').fill('7')
            await page.get_by_role('button', name='Responder').click()
            await expect(page.locator('#feedback')).to_contain_text('Correto')
            await page.get_by_role('button', name='Finalizar fase').click()
            await expect(page.locator('#feedback')).to_contain_text('Aprovado')
            self.assertEqual(errors, [])

    async def test_choice_player_keeps_exact_three_alternatives(self):
        data = {'title':'Inércia', 'topic':'Inércia', 'context':'Passageiros em um ônibus.',
                'simulation':{'scene':'inertia_bus','description':'Ônibus em movimento.','show_vectors':True,'show_live_readouts':True,'parameters':[{'key':'brake','label':'Frenagem','value':7,'unit':'m/s²','min':1,'max':10,'step':1,'hint':''}]},
                'challenge':{'prompt':'Por que o corpo tende a seguir em movimento?','answer':{'type':'choice','correct':1,'options':['A','B','C'],'explanation':'Pela inércia.'},'hint':'Primeira lei de Newton.','solution':'Inércia.'},
                'completion':{'xp':30,'mastery_tag':'Inércia'}}
        question = Questao.objects.create(fase=self.fase, enunciado=data['challenge']['prompt'], tipo_resposta='choice', codigo_fonte='browser-choice', dados_dinamicos=data)
        for index, text in enumerate(['A','B','C']):
            Opcao.objects.create(questao=question, texto=text, ordem=index+1, e_correta=index==1)
        async with self.browser_page() as (page, errors):
            await self.login(page)
            await page.goto(self.live_server_url + reverse('physics_player', args=[self.fase.id]))
            await expect(page.locator('.choice')).to_have_count(3)
            await page.locator('.choice').nth(1).click()
            await page.get_by_role('button', name='Responder').click()
            await expect(page.locator('#feedback')).to_contain_text('Correto')
            self.assertEqual(errors, [])