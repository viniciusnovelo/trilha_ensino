# Catálogo inicial do Ensino Médio

O Trilha Ensino organiza o conteúdo dos alunos em:

**Matéria → Jogo/Trilha → Módulos → Fases → Questões**

Cada jogo possui uma jornada progressiva: o primeiro módulo começa liberado e os módulos seguintes são desbloqueados automaticamente quando o módulo anterior é concluído.

O catálogo inicial possui:

- 4 matérias: Matemática, Física, Geografia e Biologia.
- 3 jogos por matéria.
- 4 módulos por jogo.
- 3 fases por módulo.
- 4 questões por fase.
- 12 fases e 48 questões por jogo.

Total: **4 matérias, 12 jogos, 48 módulos, 144 fases, 576 questões e 2.304 alternativas**.

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

## Atualização de feedback

Para atualizar apenas as explicações das questões existentes, sem recriar a estrutura:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --atualizar-feedback
```

Essa operação depende de as questões existentes continuarem correspondendo à estrutura do catálogo. Para sincronizar também módulos, fases e alternativas, use `--replace`.
