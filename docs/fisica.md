# Módulo 1 de Física — instalação e reset local

A branch `feat/usuarios-autenticacao` contém as fontes originais do Módulo 1 e a implementação integrada ao Django.

## Procedimento

Na raiz do repositório, com o ambiente virtual ativado:

```bash
git pull --ff-only origin feat/usuarios-autenticacao

python scripts/reset_e_importar_fisica.py --dry-run

python scripts/reset_e_importar_fisica.py
```

O `--dry-run` valida os arquivos-fonte, os 28 JSONs do ZIP, a correspondência entre JSON e ZIP, as 4 fases, os 21 exercícios numéricos, os 7 de múltipla escolha, as 26 cenas e as 21 fórmulas. Não apaga o banco, não executa migrations e não cria registros.

O último comando apaga completamente o `db.sqlite3` local e recria o banco pelas migrations antes de importar o Módulo 1 de Física. **Todos os usuários, dados, trilhas, módulos, fases, questões, progresso, tentativas e respostas existentes nesse banco serão perdidos.** Não é criado backup obrigatório.

Ao final, o script valida a estrutura e gera `fisica_reset_resultado.json` e `fisica_reset_resultado.txt` na raiz do projeto.

## Conteúdo esperado

- 1 matéria: Física
- 1 disciplina vinculada à matéria Física
- 1 módulo: Módulo 1
- 4 fases: Cinemática (6), Dinâmica (6), Trabalho, Energia e Potência (8), Gravitação Universal (8)
- 28 questões: 21 numéricas e 7 de múltipla escolha
- alternativas somente nas questões de múltipla escolha
- 26 identificadores de cenas e 21 fórmulas na whitelist

O conteúdo das questões é importado sem reescrever enunciados, parâmetros, respostas, tolerâncias, dicas, soluções, XP, mastery tags ou flags da simulação. As fórmulas são selecionadas por identificador em uma whitelist explícita; nenhuma expressão do JSON é executada com `eval()`.

## Testes

```bash
python -m unittest curriculo.tests_physics -v
python manage.py test curriculo.tests_physics_django
python manage.py test curriculo.browser_tests_physics
```

O teste de navegador requer Playwright e Chromium instalados. Os testes Django requerem as dependências do projeto e as migrations aplicadas.
