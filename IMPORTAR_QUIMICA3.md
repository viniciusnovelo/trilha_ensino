# Importação da Química 3

A Química 3 foi integrada como disciplina independente (`quimica-3`), sem substituir Química 1 ou Química 2.

## Fontes incluídas

- `modulo3_quimica.json`: fonte principal com 5 fases e 38 exercícios.
- `exercicios/manifest_quimica3.json`: manifesto dos 38 arquivos individuais.
- `exercicios/fase-*/`: exercícios individuais extraídos do pacote fornecido.
- `fontes/quimica3/index.html`: simulador-fonte com as cenas interativas.
- `curriculo/chem3_engine.py`: fórmulas e validação de respostas.
- `curriculo/chem3_views.py` e `curriculo/templates/curriculo/chem3_player.html`: player e endpoints.
- `curriculo/management/commands/carregar_quimica3.py`: importador com validação prévia.

## Atualizar e validar

Na raiz do projeto:

```bash
git pull --ff-only origin feat/modulo3-fisica
python manage.py check
python manage.py carregar_quimica3 --dry-run
```

Se a validação terminar com sucesso, importar:

```bash
python manage.py carregar_quimica3
```

O `--dry-run` confere JSON, manifesto, 38 arquivos individuais, fórmulas, parâmetros e cenas do simulador sem gravar no banco. A importação real usa transação e atualiza somente a disciplina `quimica-3`.

Se o dry-run falhar, não execute a importação real; envie o traceback para correção.
