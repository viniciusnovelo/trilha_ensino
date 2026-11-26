# Importação da Química 2

A Química 2 foi preparada para ser importada sem apagar ou substituir outros módulos.

## Arquivos incluídos

- `modulo2_quimica.json`: fonte principal com 5 fases e 34 exercícios.
- `exercicios/manifest.json`: manifesto dos 34 exercícios individuais.
- `exercicios/fase-*/`: cópias individuais dos exercícios para conferência de integridade.
- `fontes/quimica2/index.html`: simulador-fonte original usado como referência das cenas.
- `curriculo/chem2_engine.py`, `curriculo/chem2_views.py` e `curriculo/templates/curriculo/chem2_player.html`: motor, endpoints e player Django.
- `curriculo/management/commands/carregar_quimica2.py`: importador com validação prévia.

## Comandos

Na raiz do projeto, depois de atualizar a branch:

```bash
git pull --ff-only origin feat/modulo3-fisica
python manage.py check
python manage.py carregar_quimica2 --dry-run
python manage.py carregar_quimica2
```

O `--dry-run` valida o JSON principal, o manifesto, os 34 arquivos individuais, os tipos de resposta, as fórmulas, os parâmetros e a presença das cenas no simulador-fonte. Ele não grava nada no banco.

A importação real usa transação e atualiza/cria somente os registros identificados como Química 2. Não executa reset do banco nem remove Química 1 ou outros módulos.

Se o `dry-run` apontar divergência, não execute a importação real; envie o erro para correção.
