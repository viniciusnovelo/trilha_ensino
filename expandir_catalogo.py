import argparse
import os
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.db import transaction
from curriculo.models import Disciplina, Modulo, Fase, Questao, Opcao


# Cada jogo recebe 2 módulos novos.
# Cada módulo recebe 1 fase com 3 questões.
# A expansão é incremental e preserva todo o conteúdo existente.
DADOS = {
    "Mestre das Funções": [
        ("Gráficos e transformação", [
            ("No gráfico de f(x)=2x+3, qual é a ordenada da interseção com o eixo y?", "3", ["2", "-3", "0"]),
            ("Qual ponto pertence ao gráfico de g(x)=x-4?", "(4,0)", ["(0,4)", "(4,4)", "(-4,0)"]),
            ("A função h(x)=f(x)+5, em relação a f(x), desloca o gráfico:", "5 unidades para cima", ["5 unidades para baixo", "5 unidades para a direita", "5 unidades para a esquerda"]),
        ]),
        ("Modelagem e análise de situações", [
            ("Uma corrida cobra R$12 de taxa fixa e R$4 por quilômetro. Qual o custo de 7 km?", "R$40", ["R$28", "R$36", "R$44"]),
            ("Considerando A(x)=20+3x, qual é o custo do plano A para x=6?", "R$38", ["R$18", "R$23", "R$50"]),
            ("Uma empresa tem receita R(x)=18x e custo C(x)=6x+60. Qual é o lucro em 10 unidades?", "R$60", ["R$90", "R$120", "R$180"]),
        ]),
    ],
    "Desafio das Equações": [
        ("Equações com parênteses e frações", [
            ("Qual é a solução de 3(x+2)=21?", "5", ["3", "7", "9"]),
            ("Qual é a solução de 2(x-3)+4=12?", "7", ["5", "6", "8"]),
            ("Qual é a solução de x/3+2=6?", "12", ["8", "10", "14"]),
        ]),
        ("Sistemas e problemas", [
            ("No sistema x+y=10 e x-y=2, qual é o valor de x?", "6", ["4", "5", "8"]),
            ("Dois números têm soma 18 e diferença 4. Qual é o maior?", "11", ["7", "9", "13"]),
            ("Uma caneta custa R$2 e um caderno R$8. Uma compra com 3 canetas e 2 cadernos custa:", "R$22", ["R$18", "R$20", "R$24"]),
        ]),
    ],
    "Expedição Geométrica": [
        ("Semelhança e escala", [
            ("Em duas figuras semelhantes, a razão dos comprimentos é 2. Um lado menor de 5 cm corresponde a:", "10 cm", ["7 cm", "8 cm", "12 cm"]),
            ("Uma planta está na escala 1:100. Um segmento de 3 cm representa:", "3 m", ["30 cm", "1 m", "30 m"]),
            ("Dois triângulos semelhantes têm lados correspondentes 4 cm e 6 cm. A razão menor/maior é:", "2/3", ["1/2", "3/2", "4/3"]),
        ]),
        ("Áreas e volumes", [
            ("A área de um retângulo de 8 cm por 5 cm é:", "40 cm²", ["13 cm²", "26 cm²", "80 cm²"]),
            ("Um círculo de raio 3 cm tem área aproximada, usando π≈3,14, de:", "28,26 cm²", ["9,42 cm²", "18,84 cm²", "37,68 cm²"]),
            ("Um cubo com aresta de 4 cm tem volume de:", "64 cm³", ["16 cm³", "32 cm³", "48 cm³"]),
        ]),
    ],
    "Corrida Cinemática": [
        ("Velocidade média e gráficos", [
            ("Um carro percorre 120 km em 2 h. Sua velocidade média é:", "60 km/h", ["40 km/h", "50 km/h", "80 km/h"]),
            ("Em um gráfico posição × tempo, uma reta com inclinação constante representa:", "velocidade constante", ["aceleração constante", "posição sempre zero", "ausência de movimento"]),
            ("Um ciclista passa de 10 m para 70 m em 6 s. O deslocamento é:", "60 m", ["50 m", "70 m", "80 m"]),
        ]),
        ("Aceleração e movimento uniformemente variado", [
            ("Um veículo passa de 10 m/s para 30 m/s em 5 s. A aceleração média é:", "4 m/s²", ["2 m/s²", "6 m/s²", "8 m/s²"]),
            ("No movimento uniformemente variado, a grandeza que permanece constante é:", "aceleração", ["posição", "velocidade", "deslocamento"]),
            ("Um objeto parte do repouso com aceleração de 2 m/s². Após 4 s, sua velocidade será:", "8 m/s", ["2 m/s", "4 m/s", "6 m/s"]),
        ]),
    ],
    "Mestre das Forças": [
        ("Leis de Newton", [
            ("A primeira lei de Newton é conhecida como princípio da:", "inércia", ["ação e reação", "gravitação", "energia"]),
            ("Uma força resultante de 20 N atua em uma massa de 5 kg. A aceleração é:", "4 m/s²", ["2 m/s²", "5 m/s²", "10 m/s²"]),
            ("Quando uma pessoa empurra uma parede e a parede exerce força de volta, temos:", "ação e reação", ["inércia", "conservação da energia", "queda livre"]),
        ]),
        ("Atrito e equilíbrio", [
            ("O atrito entre os pneus e o solo é importante para:", "permitir tração e controle do movimento", ["eliminar a massa do carro", "aumentar sempre a velocidade", "zerar a força peso"]),
            ("Um bloco em repouso sobre uma superfície horizontal tem força resultante igual a:", "0 N", ["1 N", "igual ao peso", "igual à normal"]),
            ("Ao aumentar a força normal entre duas superfícies, o atrito máximo tende a:", "aumentar", ["diminuir", "ficar sempre zero", "mudar de direção automaticamente"]),
        ]),
    ],
    "Missão Energia": [
        ("Trabalho e energia cinética", [
            ("Uma força de 10 N desloca um objeto 5 m na mesma direção. O trabalho é:", "50 J", ["2 J", "15 J", "100 J"]),
            ("A energia cinética de um corpo depende de sua:", "massa e velocidade", ["apenas altura", "apenas massa", "temperatura"]),
            ("Se a velocidade de um objeto dobra, sua energia cinética:", "quadruplica", ["dobra", "triplica", "fica igual"]),
        ]),
        ("Potência e rendimento", [
            ("Uma máquina realiza 600 J de trabalho em 20 s. Sua potência média é:", "30 W", ["20 W", "60 W", "120 W"]),
            ("Um equipamento recebe 1000 J e fornece 800 J de energia útil. O rendimento é:", "80%", ["20%", "50%", "125%"]),
            ("Para realizar o mesmo trabalho em metade do tempo, a potência média necessária deve ser:", "o dobro", ["metade", "a mesma", "quatro vezes maior"]),
        ]),
    ],
    "Explorador do Espaço Geográfico": [
        ("População e urbanização", [
            ("Êxodo rural é o deslocamento de pessoas:", "do campo para a cidade", ["da cidade para o campo", "entre países somente", "entre continentes somente"]),
            ("O crescimento da população e da área construída de uma cidade caracteriza:", "urbanização", ["desertificação", "erosão", "intemperismo"]),
            ("A densidade demográfica relaciona principalmente:", "população e área", ["temperatura e altitude", "PIB e inflação", "chuva e relevo"]),
        ]),
        ("Território, redes e globalização", [
            ("Território é um espaço marcado principalmente por:", "relações de poder e controle", ["ausência de relações de poder", "apenas características naturais", "somente clima"]),
            ("Portos, rodovias e aeroportos integram:", "redes de circulação", ["apenas áreas rurais", "somente fronteiras naturais", "somente redes sociais"]),
            ("A globalização amplia a:", "interdependência entre territórios", ["isolação entre mercados", "desconexão tecnológica", "eliminação dos fluxos internacionais"]),
        ]),
    ],
    "Atlas em Ação": [
        ("Cartografia e coordenadas", [
            ("As linhas de latitude são medidas a partir do:", "Equador", ["Meridiano de Greenwich", "Trópico de Capricórnio", "Polo Norte"]),
            ("As longitudes são medidas a partir do:", "Meridiano de Greenwich", ["Equador", "Trópico de Câncer", "Círculo Polar Ártico"]),
            ("A legenda de um mapa serve para:", "explicar símbolos e convenções", ["indicar somente o norte", "calcular automaticamente a população", "alterar a escala"]),
        ]),
        ("Escalas e interpretação", [
            ("Em uma escala 1:50.000, 1 cm no mapa representa:", "500 m", ["50 m", "5 km", "50 km"]),
            ("Uma distância de 4 cm em uma escala 1:100.000 corresponde a:", "4 km", ["400 m", "40 km", "100 km"]),
            ("Um mapa em escala grande costuma apresentar:", "maior detalhamento local", ["menor detalhamento", "apenas continentes", "nenhuma informação de localização"]),
        ]),
    ],
    "Geopolítica em Jogo": [
        ("Blocos e comércio internacional", [
            ("Um bloco econômico busca, entre outros objetivos:", "facilitar relações econômicas entre membros", ["reduzir a integração entre membros", "eliminar toda produção interna", "impedir qualquer circulação"]),
            ("Uma tarifa de importação pode:", "encarecer produtos importados", ["reduzir automaticamente todo preço importado", "eliminar moedas nacionais", "aumentar a altitude"]),
            ("A balança comercial compara principalmente:", "exportações e importações de bens", ["temperatura e umidade", "população e território", "natalidade e mortalidade"]),
        ]),
        ("Conflitos, fronteiras e poder", [
            ("Uma fronteira internacional é:", "um limite político entre territórios", ["sempre uma formação natural", "sinônimo de região climática", "um tipo de relevo"]),
            ("Um conflito por território pode envolver:", "disputas por recursos, identidade ou soberania", ["somente fatores climáticos", "apenas fenômenos astronômicos", "somente atividades agrícolas"]),
            ("Soberania de um Estado refere-se principalmente à:", "capacidade de exercer autoridade sobre seu território", ["obrigação de não possuir leis", "eliminação das fronteiras", "ausência de população"]),
        ]),
    ],
    "Jornada da Célula": [
        ("Metabolismo celular", [
            ("A organela associada à maior parte da produção de ATP na respiração aeróbia é a:", "mitocôndria", ["ribossomo", "lisossomo", "vacúolo"]),
            ("Na respiração celular, a glicose é degradada para:", "liberar energia aproveitável pela célula", ["produzir DNA diretamente", "impedir a formação de ATP", "formar apenas sais minerais"]),
            ("A fermentação é uma via de obtenção de energia que:", "não depende da cadeia respiratória aeróbia", ["elimina toda produção de energia", "ocorre somente em células sem membrana", "destrói o DNA"]),
        ]),
        ("Divisão celular", [
            ("A mitose normalmente produz:", "duas células geneticamente semelhantes à célula inicial", ["quatro células sempre diferentes", "uma célula sem DNA", "apenas gametas"]),
            ("A meiose está diretamente relacionada à formação de:", "gametas", ["hemácias", "tecido ósseo", "enzimas digestivas"]),
            ("Uma diferença importante é que a meiose:", "possui duas divisões sucessivas", ["ocorre apenas em bactérias", "não envolve cromossomos", "produz sempre duas células"]),
        ]),
    ],
    "Código da Vida": [
        ("Genética e heredogramas", [
            ("O conjunto de alelos de um indivíduo para determinado gene corresponde ao:", "genótipo", ["fenótipo", "cariótipo ambiental", "ecossistema"]),
            ("Uma pessoa com dois alelos iguais para um gene é:", "homozigota", ["heterozigota", "haploide obrigatoriamente", "mutante obrigatoriamente"]),
            ("Em um heredograma, um quadrado geralmente representa:", "um homem", ["uma mulher", "uma característica dominante", "um cromossomo"]),
        ]),
        ("Probabilidade e herança", [
            ("No cruzamento Aa × Aa, a probabilidade de um descendente ser aa é:", "25%", ["0%", "50%", "75%"]),
            ("No cruzamento Aa × aa, a probabilidade de obter Aa é:", "50%", ["25%", "75%", "100%"]),
            ("Se B é dominante e bb é recessivo, um indivíduo Bb apresenta fenótipo:", "dominante", ["recessivo sempre", "sem característica", "indeterminado no modelo"]),
        ]),
    ],
    "Ecossistemas em Ação": [
        ("Cadeias e teias alimentares", [
            ("Em uma cadeia alimentar, os produtores geralmente são:", "organismos autotróficos", ["animais carnívoros", "decompositores", "parasitas"]),
            ("A principal fonte de energia para a maioria dos ecossistemas é:", "Sol", ["vento", "solo", "decompositores"]),
            ("Os decompositores têm papel importante porque:", "reciclam matéria orgânica", ["impedem a decomposição", "produzem toda a luz", "eliminam os nutrientes"]),
        ]),
        ("Ciclos e impactos ambientais", [
            ("O desmatamento pode reduzir a biodiversidade porque:", "elimina ou fragmenta habitats", ["sempre cria novos habitats", "aumenta todas as populações", "não altera recursos"]),
            ("O ciclo da água inclui processos como:", "evaporação e precipitação", ["fotossíntese e mitose apenas", "respiração e digestão apenas", "combustão e fusão nuclear"]),
            ("O excesso de nutrientes em ambientes aquáticos pode causar:", "eutrofização", ["formação de montanhas", "redução da gravidade", "desaparecimento da água"]),
        ]),
    ],
}


def embaralhar_opcoes(corretor, erradas, seed_text):
    opcoes = [corretor] + list(erradas)
    random.Random(seed_text).shuffle(opcoes)
    return opcoes


def validar_dados():
    if len(DADOS) != 12:
        raise ValueError("A expansão deve conter exatamente 12 jogos.")

    modulos = fases = questoes = 0

    for nome_jogo, modulos_jogo in DADOS.items():
        if len(modulos_jogo) != 2:
            raise ValueError("%s deve possuir 2 módulos novos." % nome_jogo)

        for titulo_modulo, lista_questoes in modulos_jogo:
            if len(lista_questoes) != 3:
                raise ValueError(
                    "%s / %s deve possuir 3 questões."
                    % (nome_jogo, titulo_modulo)
                )

            modulos += 1
            fases += 1
            questoes += len(lista_questoes)

            for pergunta, correta, erradas in lista_questoes:
                if len(erradas) != 3:
                    raise ValueError("Questão com número inválido de alternativas: %s" % pergunta)

    if (modulos, fases, questoes) != (24, 24, 72):
        raise ValueError(
            "Estrutura inválida: módulos=%s, fases=%s, questões=%s."
            % (modulos, fases, questoes)
        )


def executar(dry_run=False):
    validar_dados()

    faltantes = [
        nome for nome in DADOS
        if not Disciplina.objects.filter(nome=nome).exists()
    ]

    if faltantes:
        raise RuntimeError(
            "Jogos não encontrados no banco: " + ", ".join(faltantes)
        )

    print("")
    print("EXPANSÃO DO CATÁLOGO DO ENSINO MÉDIO")
    print("=====================================")
    print("12 jogos | 24 módulos | 24 fases | 72 questões | 288 alternativas")

    if dry_run:
        print("")
        print("DRY-RUN: nenhuma alteração será feita.")
        for nome in DADOS:
            print("  OK:", nome)
        return

    criados = {
        "modulos": 0,
        "fases": 0,
        "questoes": 0,
        "opcoes": 0,
    }

    with transaction.atomic():
        for nome_jogo, modulos_jogo in DADOS.items():
            disciplina = Disciplina.objects.get(nome=nome_jogo)

            for ordem_modulo, (titulo_modulo, lista_questoes) in enumerate(
                modulos_jogo,
                start=3,
            ):
                modulo, novo_modulo = Modulo.objects.get_or_create(
                    disciplina=disciplina,
                    ordem=ordem_modulo,
                    defaults={
                        "titulo": titulo_modulo,
                        "descricao": "Continuação e aprofundamento do conteúdo da trilha.",
                    },
                )

                if not novo_modulo and modulo.titulo != titulo_modulo:
                    raise RuntimeError(
                        "%s: a ordem %s já pertence ao módulo '%s'."
                        % (nome_jogo, ordem_modulo, modulo.titulo)
                    )

                if novo_modulo:
                    criados["modulos"] += 1

                fase, nova_fase = Fase.objects.get_or_create(
                    modulo=modulo,
                    ordem=1,
                    defaults={
                        "titulo": "Desafio de aprofundamento",
                        "tipo": "quiz",
                        "xp_recompensa": 80 if ordem_modulo == 3 else 85,
                        "moedas_recompensa": 16 if ordem_modulo == 3 else 17,
                        "deslocamento_y": 35 if ordem_modulo == 3 else -35,
                    },
                )

                if not nova_fase:
                    continue

                criados["fases"] += 1

                for indice, (pergunta, correta, erradas) in enumerate(
                    lista_questoes,
                    start=1,
                ):
                    questao = Questao.objects.create(
                        fase=fase,
                        enunciado=pergunta,
                        explicacao_erro=(
                            "Revise o conceito relacionado a esta questão. "
                            "A resposta correta é: %s."
                            % correta
                        ),
                    )
                    criados["questoes"] += 1

                    opcoes = embaralhar_opcoes(
                        correta,
                        erradas,
                        "%s|%s|%s" % (nome_jogo, titulo_modulo, indice),
                    )

                    Opcao.objects.bulk_create(
                        [
                            Opcao(
                                questao=questao,
                                texto=opcao,
                                e_correta=(opcao == correta),
                            )
                            for opcao in opcoes
                        ]
                    )
                    criados["opcoes"] += 4

    print("")
    print("EXPANSÃO CONCLUÍDA COM SUCESSO")
    print("Módulos criados:", criados["modulos"])
    print("Fases criadas:", criados["fases"])
    print("Questões criadas:", criados["questoes"])
    print("Alternativas criadas:", criados["opcoes"])


def main():
    parser = argparse.ArgumentParser(
        description="Adiciona 2 módulos e 6 questões a cada um dos 12 jogos."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida os jogos sem alterar o banco.",
    )
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
