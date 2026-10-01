# Catálogo inicial do Ensino Médio

O Trilha Ensino organiza o conteúdo dos alunos em:

**Matéria → Jogo/Trilha → Módulos → Fases → Questões**

O catálogo inicial possui:

- 4 matérias: Matemática, Física, Geografia e Biologia.
- 3 jogos por matéria.
- 2 módulos por jogo.
- 3 fases por módulo.
- 4 questões por fase.

Total: **4 matérias, 12 jogos, 24 módulos, 72 fases, 288 questões e 1.152 alternativas**.

## Importação

Valide primeiro sem alterar o banco:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --dry-run
```

Para importar os jogos que ainda não existem:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel
```

Para recriar os jogos que já possuem o mesmo slug e sincronizar integralmente a estrutura do JSON:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --replace
```

O parâmetro `--replace` apaga e recria apenas os jogos que possuem os slugs presentes no JSON. As matérias são criadas ou atualizadas automaticamente.

O importador individual `importar_trilha.py` continua funcionando para arquivos como `dados_funcoes.json`.
