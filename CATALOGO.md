# Catálogo inicial do Ensino Médio

O Trilha Ensino organiza o conteúdo dos alunos em:

**Matéria → Jogo/Trilha → Módulos → Fases → Questões**

Cada jogo possui uma jornada progressiva: o primeiro módulo começa liberado e os módulos seguintes são desbloqueados automaticamente quando o módulo anterior é concluído.

## Estrutura do catálogo

O catálogo inicial possui:

- **4 matérias:** Matemática, Física, Geografia e Biologia.
- **3 jogos por matéria:** 12 jogos no total.
- **4 módulos por jogo.**
- **3 fases por módulo.**
- **4 questões por fase.**
- **4 alternativas por questão.**
- **12 fases e 48 questões por jogo.**

Total:

**4 matérias, 12 jogos, 48 módulos, 144 fases, 576 questões e 2.304 alternativas.**

As questões que já faziam parte do catálogo anterior são preservadas. Cada módulo agora possui três fases, e cada fase possui quatro questões, com continuidade e aprofundamento dos temas do jogo. As questões possuem explicações pedagógicas estruturadas em:

- **Como pensar**
- **Passo a passo**
- **Conclusão**

## Importação

Valide primeiro sem alterar o banco:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --dry-run
```

Para importar o catálogo completo em um banco vazio:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel
```

Para recriar os jogos que já possuem o mesmo slug e sincronizar integralmente a estrutura do JSON:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --replace
```

Sem `--replace`, o importador sincroniza matérias, jogos, módulos, fases, questões e alternativas existentes, criando o que estiver faltando e preservando os IDs e o progresso já registrado. O parâmetro `--replace` continua sendo destrutivo para os jogos indicados e pode remover progresso associado às suas fases.

As matérias são criadas ou atualizadas automaticamente.

O importador individual `importar_trilha.py` continua funcionando para arquivos como `dados_funcoes.json`.

## Alternativas das questões

Cada questão do catálogo possui quatro alternativas e exatamente uma resposta correta.

Em cada fase, a posição da alternativa correta é distribuída entre as três questões:

- 1ª questão → alternativa correta na 1ª posição.
- 2ª questão → alternativa correta na 2ª posição.
- 3ª questão → alternativa correta na 3ª posição.

O campo `ordem` registra explicitamente a posição de exibição da alternativa.

## Feedback pedagógico

As explicações são armazenadas no campo `explicacao_erro` e exibidas ao aluno quando a resposta é verificada e novamente no resultado final da fase.

O formato esperado pelo catálogo contém:

```text
Como pensar: ...
Passo a passo:
1. ...
2. ...
3. ...
Conclusão: ...
```

Para atualizar somente as explicações das questões existentes, sem recriar a estrutura:

```powershell
python importar_catalogo.py dados_catalogo_ensino_medio.json --autor vilel --atualizar-feedback
```

Essa operação depende de as questões existentes continuarem correspondendo à estrutura do catálogo. Como o banco usado para a nova carga está vazio, a importação normal é o caminho adequado.
