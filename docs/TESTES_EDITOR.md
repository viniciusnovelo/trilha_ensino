# Testes de navegador do editor

A suíte de regressão do editor usa **Playwright para Python** com a API
assíncrona, integrada ao StaticLiveServerTestCase do Django.

## Por que essa abordagem

O projeto já usa o runner de testes do Django e não possuía infraestrutura de
browser. Em vez de introduzir pytest, pytest-django ou Selenium, os testes
integram o Playwright ao runner existente.

Os métodos de teste são assíncronos porque a API assíncrona do Playwright
mantém seu event loop no próprio teste. Isso evita executar o ORM síncrono do
Django dentro de um event loop ativo, problema encontrado na primeira execução
da suíte.

StaticLiveServerTestCase sobe um servidor HTTP real durante o teste. Cada caso
usa o banco de testes temporário do Django, nunca o db.sqlite3 de
desenvolvimento, e cria sua própria trilha, módulo, fase e questão.

Cada teste também cria um contexto novo do Chromium, evitando cookies e estado
de página compartilhados.

## Instalação local

Ative o ambiente virtual e instale as dependências:

    python -m pip install -r requirements.txt
    python -m playwright install chromium

No Linux/CI, para instalar também as dependências do sistema:

    python -m playwright install --with-deps chromium

## Executar

Testes Django existentes:

    python manage.py test curriculo gamificacao

Suíte de navegador do editor:

    python manage.py test curriculo.browser_tests

Um teste específico:

    python manage.py test curriculo.browser_tests.EditorBrowserTests.test_modal_de_modulo_fica_visivel_e_persiste_edicao

Para abrir o Chromium durante o desenvolvimento:

    $env:PLAYWRIGHT_HEADLESS="0"
    python manage.py test curriculo.browser_tests

O padrão é headless.

## Cobertura

A suíte contém 12 testes e cobre:

- acesso autenticado ao editor;
- seleção de módulo, fase e questão;
- expansão/recolhimento independente de módulos e fases;
- abertura automática da hierarquia ao selecionar fase ou questão;
- painel de detalhes contextual, recolhível e com ganho de espaço para o mapa;
- sincronização visual entre Conteúdo e Mapa;
- sincronização fase Conteúdo ↔ Mapa ↔ Detalhes;
- ausência de navegação ao clicar na fase do mapa;
- navegação explícita pelo botão "Abrir fase";
- abertura visual dos três modais;
- preenchimento inicial dos campos;
- edição, submit, reload e persistência de módulo, fase e questão;
- exclusão de questão com confirmação;
- zoom para menos, zoom para mais e Ajustar;
- arraste vertical de fase e persistência do deslocamento_y;
- captura de erros JavaScript não tratados durante os fluxos.

A URL usada nos testes é a URL da trilha criada pelo próprio caso. Ela não é
fixada no ID 4 porque usar a trilha 4 do banco de desenvolvimento violaria o
isolamento solicitado.

## CI

O workflow do GitHub Actions instala o Chromium do Playwright com dependências
do sistema e executa a suíte separadamente dos testes Django convencionais.
