# Módulo 2 de Física — implementação

## Conteúdo integrado
- 4 fases: Termologia e Calorimetria (8), Termodinâmica (8), Ondulatória (10) e Óptica Geométrica (8).
- 34 questões, 17 de múltipla escolha e 17 numéricas.
- 34 cenas específicas e 17 fórmulas na whitelist do motor.
- Conteúdo fonte preservado em `modulo2_fisica.json`; HTML original em `docs/fontes/modulo2/index.html`.

## Importar sem apagar o Módulo 1
Na raiz do projeto, com o ambiente virtual ativo:
```powershell
python scripts/importar_modulo2_fisica.py --dry-run
python scripts/importar_modulo2_fisica.py
```
O importador cria/atualiza o módulo de ordem 2, as quatro fases e as 34 questões. Não apaga banco, usuários, progresso, tentativas ou o Módulo 1. Para validar também o arquivo ZIP, informe `--zip caminho\para\modulo2_exercicios.zip`.

## Correções físicas/técnicas aplicadas
- `fis2-td-05`: limite superior de Qc ajustado para 2.000 J para incluir o valor inicial de 1.500 J; o controle ainda limita Qc a Qh menos um incremento.
- `zeroth_law`: a legenda só afirma equilíbrio quando TA, TB e TT coincidem.
- `pv_process`: P e V posicionam um estado observável no diagrama P×V.
- `wave_nature` e `wave_direction`: frequência e amplitude afetam a representação.
- `wave_refraction`: frentes e comprimentos de onda dependem de v/f; a frequência permanece constante.
- `wave_diffraction` e `wave_interference`: abertura, comprimento de onda, fase e amplitude passam a alterar a geometria/resultado desenhado.
- `light_reflection_refraction`: reflexão total interna é identificada quando a lei de Snell não admite raio refratado.
- `convex_mirror`: posição e tamanho da imagem virtual dependem da distância do objeto (focal adotada no esquema: −0,5 m).
- `human_eye`: deslocamento do foco move o ponto focal em relação à retina.
- Relações entre controles são validadas no navegador e no servidor: Qc<Qh, W≤Qh, Vf>Vi e Tc<Th.

## Validação
`curriculo.physics_module2_source.validate_source` valida a fonte, a distribuição e os parâmetros. `validate_zip_archive` compara o conteúdo do ZIP exercício a exercício. Os testes automatizados estão em `curriculo/test_physics_module2.py`.
