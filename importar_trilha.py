import argparse
import json
import os
import sys
from pathlib import Path

import django


# ============================================================
# CONFIGURAÇÃO DO DJANGO
# ============================================================

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings',
)

django.setup()


from django.contrib.auth import get_user_model
from django.db import transaction

from curriculo.models import (
    Disciplina,
    Modulo,
    Fase,
    Questao,
    Opcao,
)


User = get_user_model()


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_PADRAO = 'dados_funcoes.json'

MAX_DESLOCAMENTO_Y = 150

MIN_DESLOCAMENTO_Y = -150


# ============================================================
# UTILITÁRIOS
# ============================================================

def erro(mensagem):
    """
    Exibe uma mensagem de erro e encerra o programa.
    """

    print()
    print(f'❌ ERRO: {mensagem}')
    print()

    sys.exit(1)


def carregar_json(caminho):
    """
    Carrega o arquivo JSON.
    """

    caminho = Path(caminho)

    if not caminho.exists():

        erro(
            f'O arquivo "{caminho}" não foi encontrado.'
        )

    if not caminho.is_file():

        erro(
            f'"{caminho}" não é um arquivo válido.'
        )

    try:

        with caminho.open(
            'r',
            encoding='utf-8',
        ) as arquivo:

            return json.load(arquivo)

    except json.JSONDecodeError as exc:

        erro(
            'O arquivo JSON possui erro de sintaxe. '
            f'Linha {exc.lineno}, coluna {exc.colno}.'
        )

    except OSError as exc:

        erro(
            f'Não foi possível ler o arquivo: {exc}'
        )


def obter_autor(username):
    """
    Localiza o usuário responsável pela trilha.

    Primeiro procura exatamente pelo username informado.

    Se o usuário não existir e o username solicitado for
    "vilel", tenta usar o primeiro superusuário disponível,
    mantendo a compatibilidade com o projeto original.
    """

    autor = (
        User.objects
        .filter(username=username)
        .first()
    )

    if autor:

        return autor

    if username == 'vilel':

        autor = (
            User.objects
            .filter(is_superuser=True)
            .order_by('id')
            .first()
        )

        if autor:

            print(
                f'⚠️ Usuário "vilel" não encontrado. '
                f'Usando o superusuário "{autor.username}".'
            )

            return autor

    erro(
        f'O usuário "{username}" não existe no banco de dados.'
    )


def confirmar_substituicao(trilha):
    """
    Pede confirmação antes de apagar uma trilha existente.
    """

    print()
    print(
        '⚠️ A trilha abaixo já existe:'
    )
    print(
        f'   Nome: {trilha.nome}'
    )
    print(
        f'   Slug: {trilha.slug}'
    )
    print()

    resposta = input(
        'Deseja APAGAR e importar novamente? '
        'Digite "SIM" para continuar: '
    )

    if resposta.strip().upper() != 'SIM':

        print()
        print(
            'Importação cancelada pelo usuário.'
        )
        print()

        sys.exit(0)


# ============================================================
# VALIDAÇÃO DO JSON
# ============================================================

def validar_dados(dados):
    """
    Valida o conteúdo antes de alterar o banco.

    Isso evita iniciar uma importação e descobrir um erro
    somente no meio do processo.
    """

    if not isinstance(dados, dict):

        erro(
            'O arquivo JSON deve conter um objeto na raiz.'
        )

    campos_obrigatorios = [
        'nome',
        'descricao',
        'modulos',
    ]

    for campo in campos_obrigatorios:

        if campo not in dados:

            erro(
                f'O campo obrigatório "{campo}" não foi encontrado.'
            )

    if not isinstance(
        dados['nome'],
        str,
    ) or not dados['nome'].strip():

        erro(
            'O campo "nome" precisa ser um texto não vazio.'
        )

    if not isinstance(
        dados['descricao'],
        str,
    ):

        erro(
            'O campo "descricao" precisa ser um texto.'
        )

    modulos = dados['modulos']

    if not isinstance(
        modulos,
        list,
    ) or not modulos:

        erro(
            'O arquivo precisa possuir pelo menos um módulo.'
        )

    temas_validos = {
        valor
        for valor, _ in Disciplina.TEMAS
    }

    tema = dados.get(
        'tema',
        'tema-padrao',
    )

    if tema not in temas_validos:

        erro(
            f'Tema inválido: "{tema}". '
            f'Valores permitidos: {sorted(temas_validos)}'
        )

    tipos_validos = {
        valor
        for valor, _ in Fase.TIPO_CHOICES
    }

    ordens_modulos = set()

    total_fases = 0

    total_questoes = 0

    total_opcoes = 0

    for modulo_indice, modulo in enumerate(
        modulos,
        start=1,
    ):

        if not isinstance(
            modulo,
            dict,
        ):

            erro(
                f'Módulo #{modulo_indice} inválido.'
            )

        for campo in [
            'titulo',
            'descricao',
            'ordem',
            'fases',
        ]:

            if campo not in modulo:

                erro(
                    f'Módulo #{modulo_indice} '
                    f'não possui o campo "{campo}".'
                )

        ordem_modulo = modulo['ordem']

        if not isinstance(
            ordem_modulo,
            int,
        ) or ordem_modulo < 1:

            erro(
                f'A ordem do módulo #{modulo_indice} '
                'deve ser um inteiro maior ou igual a 1.'
            )

        if ordem_modulo in ordens_modulos:

            erro(
                f'Existem dois módulos com ordem {ordem_modulo}.'
            )

        ordens_modulos.add(
            ordem_modulo
        )

        fases = modulo['fases']

        if not isinstance(
            fases,
            list,
        ) or not fases:

            erro(
                f'O módulo #{modulo_indice} '
                'precisa possuir pelo menos uma fase.'
            )

        ordens_fases = set()

        for fase_indice, fase in enumerate(
            fases,
            start=1,
        ):

            if not isinstance(
                fase,
                dict,
            ):

                erro(
                    f'Fase #{fase_indice} do módulo '
                    f'#{modulo_indice} inválida.'
                )

            for campo in [
                'titulo',
                'ordem',
                'questoes',
            ]:

                if campo not in fase:

                    erro(
                        f'A fase "{fase.get("titulo", "?")}" '
                        f'não possui o campo "{campo}".'
                    )

            ordem_fase = fase['ordem']

            if not isinstance(
                ordem_fase,
                int,
            ) or ordem_fase < 1:

                erro(
                    f'A ordem da fase '
                    f'"{fase.get("titulo", "?")}" '
                    'deve ser um inteiro maior ou igual a 1.'
                )

            if ordem_fase in ordens_fases:

                erro(
                    f'O módulo "{modulo["titulo"]}" '
                    f'possui duas fases com ordem {ordem_fase}.'
                )

            ordens_fases.add(
                ordem_fase
            )

            tipo = fase.get(
                'tipo',
                'quiz',
            )

            if tipo not in tipos_validos:

                erro(
                    f'A fase "{fase["titulo"]}" '
                    f'possui tipo inválido: "{tipo}".'
                )

            deslocamento_y = fase.get(
                'deslocamento_y',
                0,
            )

            if not isinstance(
                deslocamento_y,
                int,
            ):

                erro(
                    f'O deslocamento_y da fase '
                    f'"{fase["titulo"]}" deve ser inteiro.'
                )

            if not (
                MIN_DESLOCAMENTO_Y
                <= deslocamento_y
                <= MAX_DESLOCAMENTO_Y
            ):

                erro(
                    f'O deslocamento_y da fase '
                    f'"{fase["titulo"]}" deve estar entre '
                    f'{MIN_DESLOCAMENTO_Y} e '
                    f'{MAX_DESLOCAMENTO_Y}.'
                )

            xp = fase.get(
                'xp_recompensa',
                50,
            )

            moedas = fase.get(
                'moedas_recompensa',
                10,
            )

            if not isinstance(
                xp,
                int,
            ) or xp < 0:

                erro(
                    f'O XP da fase '
                    f'"{fase["titulo"]}" é inválido.'
                )

            if not isinstance(
                moedas,
                int,
            ) or moedas < 0:

                erro(
                    f'As moedas da fase '
                    f'"{fase["titulo"]}" são inválidas.'
                )

            questoes = fase['questoes']

            if not isinstance(
                questoes,
                list,
            ) or not questoes:

                erro(
                    f'A fase "{fase["titulo"]}" '
                    'precisa possuir pelo menos uma questão.'
                )

            total_fases += 1

            for questao_indice, questao in enumerate(
                questoes,
                start=1,
            ):

                if not isinstance(
                    questao,
                    dict,
                ):

                    erro(
                        f'Questão #{questao_indice} da fase '
                        f'"{fase["titulo"]}" inválida.'
                    )

                for campo in [
                    'enunciado',
                    'explicacao_erro',
                    'opcoes',
                ]:

                    if campo not in questao:

                        erro(
                            f'A questão #{questao_indice} '
                            f'da fase "{fase["titulo"]}" '
                            f'não possui "{campo}".'
                        )

                opcoes = questao['opcoes']

                if not isinstance(
                    opcoes,
                    list,
                ):

                    erro(
                        f'As opções da questão #{questao_indice} '
                        f'da fase "{fase["titulo"]}" '
                        'devem ser uma lista.'
                    )

                if len(opcoes) < 2:

                    erro(
                        f'A questão #{questao_indice} da fase '
                        f'"{fase["titulo"]}" precisa possuir '
                        'pelo menos duas alternativas.'
                    )

                if len(opcoes) > 4:

                    erro(
                        f'A questão #{questao_indice} da fase '
                        f'"{fase["titulo"]}" possui mais de '
                        'quatro alternativas. '
                        'O editor atual trabalha com até 4.'
                    )

                quantidade_corretas = 0

                for opcao_indice, opcao in enumerate(
                    opcoes,
                    start=1,
                ):

                    if not isinstance(
                        opcao,
                        dict,
                    ):

                        erro(
                            f'Opção #{opcao_indice} da questão '
                            f'#{questao_indice} inválida.'
                        )

                    if 'texto' not in opcao:

                        erro(
                            f'Opção #{opcao_indice} da questão '
                            f'#{questao_indice} não possui "texto".'
                        )

                    if 'correta' not in opcao:

                        erro(
                            f'Opção #{opcao_indice} da questão '
                            f'#{questao_indice} não possui "correta".'
                        )

                    if not isinstance(
                        opcao['correta'],
                        bool,
                    ):

                        erro(
                            f'O campo "correta" da opção '
                            f'#{opcao_indice} deve ser true ou false.'
                        )

                    if opcao['correta']:

                        quantidade_corretas += 1

                    total_opcoes += 1

                if quantidade_corretas != 1:

                    erro(
                        f'A questão #{questao_indice} da fase '
                        f'"{fase["titulo"]}" deve possuir exatamente '
                        f'uma alternativa correta, mas possui '
                        f'{quantidade_corretas}.'
                    )

                total_questoes += 1

    print()
    print('✅ Validação concluída.')
    print(
        f'   Módulos: {len(modulos)}'
    )
    print(
        f'   Fases: {total_fases}'
    )
    print(
        f'   Questões: {total_questoes}'
    )
    print(
        f'   Alternativas: {total_opcoes}'
    )
    print()

    return {
        'modulos': len(modulos),
        'fases': total_fases,
        'questoes': total_questoes,
        'opcoes': total_opcoes,
    }


# ============================================================
# IMPORTAÇÃO
# ============================================================

def importar_dados(
    dados,
    autor,
    replace=False,
    dry_run=False,
):
    """
    Importa a trilha completa dentro de uma transação.

    Se ocorrer qualquer erro durante a importação,
    nenhuma parte será mantida no banco.
    """

    slug = dados.get(
        'slug',
        ''
    ).strip()

    if not slug:

        from django.utils.text import slugify

        slug = slugify(
            dados['nome']
        )

    trilha_existente = (
        Disciplina.objects
        .filter(slug=slug)
        .first()
    )

    if trilha_existente:

        if not replace:

            erro(
                f'Já existe uma trilha com slug "{slug}". '
                'Use --replace para substituí-la.'
            )

        confirmar_substituicao(
            trilha_existente
        )

    if dry_run:

        print(
            '🧪 DRY-RUN: nenhuma alteração será feita no banco.'
        )

        return

    with transaction.atomic():

        if trilha_existente:

            trilha_existente.delete()

            print(
                f'🗑️ Trilha anterior "{slug}" removida.'
            )

        trilha = Disciplina.objects.create(
            autor=autor,
            nome=dados['nome'].strip(),
            slug=slug,
            descricao=dados.get(
                'descricao',
                '',
            ).strip(),
            icone=dados.get(
                'icone',
                'book',
            ),
            ordem=dados.get(
                'ordem',
                1,
            ),
            ativo=dados.get(
                'ativo',
                True,
            ),
            tema=dados.get(
                'tema',
                'tema-padrao',
            ),
        )

        print(
            f'🎮 Trilha criada: {trilha.nome}'
        )

        print(
            f'   Slug: {trilha.slug}'
        )

        print(
            f'   Tema: {trilha.tema}'
        )

        print()

        total_modulos = 0

        total_fases = 0

        total_questoes = 0

        total_opcoes = 0

        for modulo_data in sorted(
            dados['modulos'],
            key=lambda modulo: (
                modulo['ordem']
            ),
        ):

            modulo = Modulo.objects.create(
                disciplina=trilha,
                titulo=modulo_data[
                    'titulo'
                ].strip(),
                descricao=modulo_data.get(
                    'descricao',
                    '',
                ).strip(),
                ordem=modulo_data[
                    'ordem'
                ],
            )

            total_modulos += 1

            print(
                f'📦 Módulo {modulo.ordem}: '
                f'{modulo.titulo}'
            )

            for fase_data in sorted(
                modulo_data['fases'],
                key=lambda fase: (
                    fase['ordem']
                ),
            ):

                fase = Fase.objects.create(
                    modulo=modulo,
                    titulo=fase_data[
                        'titulo'
                    ].strip(),
                    ordem=fase_data[
                        'ordem'
                    ],
                    tipo=fase_data.get(
                        'tipo',
                        'quiz',
                    ),
                    xp_recompensa=fase_data.get(
                        'xp_recompensa',
                        50,
                    ),
                    moedas_recompensa=fase_data.get(
                        'moedas_recompensa',
                        10,
                    ),
                    deslocamento_y=fase_data.get(
                        'deslocamento_y',
                        0,
                    ),
                )

                total_fases += 1

                print(
                    f'   ⭐ Fase {fase.ordem}: '
                    f'{fase.titulo} '
                    f'({fase.tipo})'
                )

                for questao_data in (
                    fase_data['questoes']
                ):

                    questao = Questao.objects.create(
                        fase=fase,
                        enunciado=questao_data[
                            'enunciado'
                        ].strip(),
                        explicacao_erro=questao_data.get(
                            'explicacao_erro',
                            '',
                        ).strip(),
                    )

                    total_questoes += 1

                    for opcao_data in (
                        questao_data['opcoes']
                    ):

                        Opcao.objects.create(
                            questao=questao,
                            texto=opcao_data[
                                'texto'
                            ].strip(),
                            e_correta=opcao_data[
                                'correta'
                            ],
                        )

                        total_opcoes += 1

    print()
    print(
        '🎉 IMPORTAÇÃO CONCLUÍDA COM SUCESSO!'
    )
    print()
    print(
        f'   🎮 Trilhas: 1'
    )
    print(
        f'   📦 Módulos: {total_modulos}'
    )
    print(
        f'   ⭐ Fases: {total_fases}'
    )
    print(
        f'   ❓ Questões: {total_questoes}'
    )
    print(
        f'   🔘 Alternativas: {total_opcoes}'
    )
    print()
    print(
        f'   👨‍🏫 Autor: {autor.username}'
    )
    print(
        f'   🌎 Tema: {trilha.tema}'
    )
    print()


# ============================================================
# ATUALIZAÇÃO SEGURA DO FEEDBACK
# ============================================================

def atualizar_feedback(
    dados,
    dry_run=False,
):
    """
    Atualiza somente as explicações das questões existentes.

    A correspondência usa:
    - slug da trilha;
    - ordem do módulo;
    - ordem da fase;
    - posição da questão dentro da fase.

    Esta operação não cria, exclui ou altera alternativas,
    fases, módulos ou progresso do aluno.
    """

    slug = dados.get(
        'slug',
        ''
    ).strip()

    if not slug:
        from django.utils.text import slugify
        slug = slugify(dados['nome'])

    trilha = (
        Disciplina.objects
        .filter(slug=slug)
        .first()
    )

    if trilha is None:
        erro(
            f'Não existe uma trilha com slug "{slug}" '
            'para receber a atualização de feedback.'
        )

    atualizadas = 0
    sem_correspondencia = []

    for modulo_data in sorted(
        dados['modulos'],
        key=lambda item: item['ordem'],
    ):
        modulo = (
            trilha.modulos
            .filter(
                ordem=modulo_data['ordem']
            )
            .order_by('id')
            .first()
        )

        if modulo is None:
            sem_correspondencia.append(
                f'módulo:{modulo_data["ordem"]}'
            )
            continue

        for fase_data in sorted(
            modulo_data['fases'],
            key=lambda item: item['ordem'],
        ):
            fase = (
                modulo.fases
                .filter(
                    ordem=fase_data['ordem']
                )
                .order_by('id')
                .first()
            )

            if fase is None:
                sem_correspondencia.append(
                    (
                        f'módulo:{modulo.ordem}:'
                        f'fase:{fase_data["ordem"]}'
                    )
                )
                continue

            questoes = list(
                fase.questoes
                .order_by('id')
            )

            for indice, questao_data in enumerate(
                fase_data['questoes']
            ):
                if indice >= len(questoes):
                    sem_correspondencia.append(
                        (
                            f'módulo:{modulo.ordem}:'
                            f'fase:{fase.ordem}:'
                            f'questão:{indice + 1}'
                        )
                    )
                    continue

                questao = questoes[indice]

                nova_explicacao = (
                    questao_data
                    .get(
                        'explicacao_erro',
                        '',
                    )
                    .strip()
                )

                if (
                    questao.explicacao_erro
                    == nova_explicacao
                ):
                    continue

                if not dry_run:
                    questao.explicacao_erro = (
                        nova_explicacao
                    )
                    questao.save(
                        update_fields=[
                            'explicacao_erro'
                        ]
                    )

                atualizadas += 1

    print()

    if dry_run:
        print(
            '🧪 DRY-RUN: nenhuma explicação será alterada.'
        )

    print(
        f'📖 Explicações que seriam/foram atualizadas: '
        f'{atualizadas}'
    )

    if sem_correspondencia:
        print(
            '⚠️ Correspondências não encontradas: '
            + ', '.join(sem_correspondencia)
        )

    print()


# ============================================================
# ARGUMENTOS
# ============================================================

def criar_parser():
    parser = argparse.ArgumentParser(
        description=(
            'Importa uma trilha/jogo completo '
            'de um arquivo JSON para o Django.'
        )
    )

    parser.add_argument(
        'arquivo',
        nargs='?',
        default=ARQUIVO_PADRAO,
        help=(
            f'Arquivo JSON a importar. '
            f'Padrão: {ARQUIVO_PADRAO}'
        ),
    )

    parser.add_argument(
        '--autor',
        default='vilel',
        help=(
            'Username do usuário que será o autor '
            'da trilha. Padrão: vilel'
        ),
    )

    parser.add_argument(
        '--replace',
        action='store_true',
        help=(
            'Substitui uma trilha existente que '
            'tenha o mesmo slug.'
        ),
    )

    parser.add_argument(
        '--yes',
        action='store_true',
        help=(
            'Confirma automaticamente a substituição '
            'quando --replace for usado.'
        ),
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=(
            'Valida o arquivo sem alterar o banco.'
        ),
    )

    parser.add_argument(
        '--atualizar-feedback',
        action='store_true',
        help=(
            'Atualiza somente as explicações das questões existentes, '
            'sem alterar alternativas, estrutura ou progresso.'
        ),
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main():

    parser = criar_parser()

    args = parser.parse_args()

    print()
    print(
        '=============================================='
    )
    print(
        '       IMPORTADOR DE TRILHAS / JOGOS'
    )
    print(
        '=============================================='
    )

    print()
    print(
        f'📄 Arquivo: {args.arquivo}'
    )

    print(
        f'👨‍🏫 Autor: {args.autor}'
    )

    print()

    dados = carregar_json(
        args.arquivo
    )

    validar_dados(
        dados
    )

    if args.atualizar_feedback:

        if args.replace:
            erro(
                'Use --atualizar-feedback isoladamente. '
                'Ele não pode ser combinado com --replace.'
            )

        atualizar_feedback(
            dados=dados,
            dry_run=args.dry_run,
        )
        return

    autor = obter_autor(
        args.autor
    )

    if args.replace and args.yes:

        # Em modo automático, a confirmação será
        # tratada dentro da transação.
        pass

    if args.replace:

        slug = dados.get(
            'slug',
            '',
        ).strip()

        if not slug:

            from django.utils.text import slugify

            slug = slugify(
                dados['nome']
            )

        existente = (
            Disciplina.objects
            .filter(slug=slug)
            .first()
        )

        if existente and args.yes:

            print()
            print(
                f'⚠️ --replace --yes: '
                f'a trilha "{existente.nome}" será substituída.'
            )
            print()

    importar_dados(
        dados=dados,
        autor=autor,
        replace=args.replace,
        dry_run=args.dry_run,
    )


if __name__ == '__main__':
    main()