import argparse
import json
import os
import sys
from pathlib import Path

import django


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings',
)

django.setup()


from django.contrib.auth import get_user_model
from django.db import transaction

from curriculo.models import (
    Disciplina,
    Fase,
    Materia,
    Modulo,
    Opcao,
    Questao,
)


User = get_user_model()

ARQUIVO_PADRAO = 'dados_catalogo_ensino_medio.json'


def erro(mensagem):
    print()
    print(f'❌ ERRO: {mensagem}')
    print()
    sys.exit(1)


def carregar_json(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        erro(f'O arquivo "{caminho}" não foi encontrado.')

    try:
        with caminho.open('r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as exc:
        erro(
            'JSON inválido: '
            f'linha {exc.lineno}, coluna {exc.colno}.'
        )
    except OSError as exc:
        erro(f'Não foi possível ler o arquivo: {exc}')


def obter_autor(username):
    autor = User.objects.filter(username=username).first()

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
        f'O usuário "{username}" não existe no banco.'
    )


def validar_opcoes(questao, contexto):
    opcoes = questao.get('opcoes')

    if not isinstance(opcoes, list) or len(opcoes) != 4:
        erro(
            f'{contexto}: cada questão precisa de exatamente 4 opções.'
        )

    corretas = 0
    posicoes = set()
    opcoes_validadas = []

    for indice, opcao in enumerate(opcoes, start=1):
        if not isinstance(opcao, dict):
            erro(f'{contexto}: opção #{indice} inválida.')

        if not isinstance(opcao.get('texto'), str) or not opcao['texto'].strip():
            erro(f'{contexto}: opção #{indice} sem texto.')

        if not isinstance(opcao.get('correta'), bool):
            erro(
                f'{contexto}: o campo "correta" da opção #{indice} '
                'deve ser true ou false.'
            )

        ordem = opcao.get('ordem', indice)

        if not isinstance(ordem, int) or isinstance(ordem, bool):
            erro(
                f'{contexto}: o campo "ordem" da opção #{indice} '
                'deve ser um número inteiro.'
            )

        if ordem not in range(1, 5):
            erro(
                f'{contexto}: o campo "ordem" da opção #{indice} '
                'deve estar entre 1 e 4.'
            )

        if ordem in posicoes:
            erro(
                f'{contexto}: a posição {ordem} foi usada mais de uma vez.'
            )

        posicoes.add(ordem)

        opcoes_validadas.append(
            (ordem, opcao)
        )

        if opcao['correta']:
            corretas += 1

    if corretas != 1:
        erro(
            f'{contexto}: é necessário exatamente uma opção correta.'
        )

    if posicoes != {1, 2, 3, 4}:
        erro(
            f'{contexto}: as alternativas devem ocupar exatamente '
            'as posições 1, 2, 3 e 4.'
        )

    opcoes_ordenadas = sorted(
        opcoes_validadas,
        key=lambda item: item[0],
    )

    for posicao, (_, opcao) in enumerate(
        opcoes_ordenadas,
        start=1,
    ):
        if opcao['correta']:
            return posicao

    return None


def validar_catalogo(dados):
    if not isinstance(dados, dict):
        erro('A raiz do JSON deve ser um objeto.')

    materias = dados.get('materias')

    if not isinstance(materias, list) or not materias:
        erro('O catálogo precisa possuir a lista "materias".')

    slugs_materias = set()
    slugs_jogos = set()

    total_jogos = 0
    total_modulos = 0
    total_fases = 0
    total_questoes = 0
    total_opcoes = 0

    for materia_indice, materia in enumerate(materias, start=1):
        contexto_materia = f'Matéria #{materia_indice}'

        for campo in ('nome', 'slug', 'descricao', 'icone', 'ordem', 'jogos'):
            if campo not in materia:
                erro(
                    f'{contexto_materia}: campo "{campo}" ausente.'
                )

        slug_materia = materia['slug']

        if slug_materia in slugs_materias:
            erro(
                f'Duplicidade de slug de matéria: "{slug_materia}".'
            )

        slugs_materias.add(slug_materia)

        jogos = materia['jogos']

        if not isinstance(jogos, list) or not jogos:
            erro(
                f'{contexto_materia}: é necessário pelo menos um jogo.'
            )

        for jogo_indice, jogo in enumerate(jogos, start=1):
            contexto_jogo = (
                f'{contexto_materia} · Jogo #{jogo_indice}'
            )

            for campo in (
                'nome',
                'slug',
                'descricao',
                'icone',
                'ordem',
                'tema',
                'modulos',
            ):
                if campo not in jogo:
                    erro(
                        f'{contexto_jogo}: campo "{campo}" ausente.'
                    )

            if jogo['slug'] in slugs_jogos:
                erro(
                    f'Duplicidade de slug de jogo: "{jogo["slug"]}".'
                )

            slugs_jogos.add(jogo['slug'])
            total_jogos += 1

            modulos = jogo['modulos']

            if not isinstance(modulos, list) or len(modulos) != 4:
                erro(
                    f'{contexto_jogo}: cada jogo deve possuir '
                    'exatamente 4 módulos.'
                )

            ordens_modulos = set()

            fases_jogo = 0
            questoes_jogo = 0

            for modulo_indice, modulo in enumerate(modulos, start=1):
                contexto_modulo = (
                    f'{contexto_jogo} · Módulo #{modulo_indice}'
                )

                for campo in (
                    'titulo',
                    'descricao',
                    'ordem',
                    'fases',
                ):
                    if campo not in modulo:
                        erro(
                            f'{contexto_modulo}: campo "{campo}" ausente.'
                        )

                if modulo['ordem'] in ordens_modulos:
                    erro(
                        f'{contexto_modulo}: ordem duplicada.'
                    )

                ordens_modulos.add(modulo['ordem'])

                if modulo['ordem'] not in (1, 2, 3, 4):
                    erro(
                        f'{contexto_modulo}: a ordem deve estar entre 1 e 4.'
                    )

                total_modulos += 1

                fases = modulo['fases']

                if not isinstance(fases, list) or len(fases) != 3:
                    erro(
                        f'{contexto_modulo}: cada módulo deve possuir '
                        'exatamente 3 fases.'
                    )

                ordens_fases = set()

                for fase_indice, fase in enumerate(fases, start=1):
                    contexto_fase = (
                        f'{contexto_modulo} · Fase #{fase_indice}'
                    )

                    for campo in (
                        'titulo',
                        'ordem',
                        'tipo',
                        'xp_recompensa',
                        'moedas_recompensa',
                        'deslocamento_y',
                        'questoes',
                    ):
                        if campo not in fase:
                            erro(
                                f'{contexto_fase}: campo "{campo}" ausente.'
                            )

                    if fase['ordem'] in ordens_fases:
                        erro(
                            f'{contexto_fase}: ordem duplicada.'
                        )

                    ordens_fases.add(fase['ordem'])

                    if fase['ordem'] not in (1, 2, 3):
                        erro(
                            f'{contexto_fase}: a ordem deve estar entre 1 e 3.'
                        )

                    total_fases += 1
                    fases_jogo += 1

                    questoes = fase['questoes']

                    if not isinstance(questoes, list) or len(questoes) != 4:
                        erro(
                            f'{contexto_fase}: cada fase deve possuir '
                            'exatamente 4 questões.'
                        )

                    posicoes_corretas = []

                    for questao_indice, questao in enumerate(questoes, start=1):
                        contexto_questao = (
                            f'{contexto_fase} · Questão #{questao_indice}'
                        )

                        for campo in (
                            'enunciado',
                            'explicacao_erro',
                            'opcoes',
                        ):
                            if campo not in questao:
                                erro(
                                    f'{contexto_questao}: '
                                    f'campo "{campo}" ausente.'
                                )

                        explicacao = questao.get(
                            'explicacao_erro',
                            '',
                        )

                        if not isinstance(explicacao, str) or not explicacao.strip():
                            erro(
                                f'{contexto_questao}: explicação pedagógica ausente.'
                            )

                        for marcador in (
                            'Como pensar:',
                            'Passo a passo:',
                            'Conclusão:',
                        ):
                            if marcador not in explicacao:
                                erro(
                                    f'{contexto_questao}: a explicação deve '
                                    f'conter "{marcador}".'
                                )

                        posicao_correta = validar_opcoes(
                            questao,
                            contexto_questao,
                        )

                        posicoes_corretas.append(
                            posicao_correta
                        )

                        total_questoes += 1
                        questoes_jogo += 1
                        total_opcoes += 4

                    if len(set(posicoes_corretas)) != len(posicoes_corretas):
                        erro(
                            f'{contexto_fase}: a posição da resposta correta '
                            'deve variar entre as 4 questões da fase.'
                        )

    print()
    print('✅ Validação do catálogo concluída.')
    print(f'   Matérias: {len(materias)}')
    print(f'   Jogos: {total_jogos}')
    print(f'   Módulos: {total_modulos}')
    print(f'   Fases: {total_fases}')
    print(f'   Questões: {total_questoes}')
    print(f'   Alternativas: {total_opcoes}')
    print()

    if total_modulos != total_jogos * 4:
        erro(
            'A estrutura final deveria possuir 4 módulos por jogo.'
        )

    if total_fases != total_jogos * 12:
        erro(
            'A estrutura final deveria possuir 12 fases por jogo (3 por módulo).'
        )

    if total_questoes != total_jogos * 48:
        erro(
            'A estrutura final deveria possuir 48 questões por jogo (4 por fase).'
        )

    if total_opcoes != total_questoes * 4:
        erro(
            'Cada questão deve possuir exatamente 4 alternativas.'
        )

    return {
        'materias': len(materias),
        'jogos': total_jogos,
        'modulos': total_modulos,
        'fases': total_fases,
        'questoes': total_questoes,
        'opcoes': total_opcoes,
    }


def atualizar_feedback(
    dados,
    dry_run=False,
):
    """
    Atualiza somente o feedback pedagógico das questões existentes.

    A correspondência usa o slug do jogo, a ordem do módulo,
    a ordem da fase e, preferencialmente, o enunciado da questão.
    A posição dentro da fase é usada apenas como fallback quando
    o enunciado da mesma posição coincide.

    Nenhuma alternativa, fase, módulo, progresso ou recompensa
    é criada, excluída ou alterada.
    """
    atualizadas = 0
    sem_correspondencia = []

    def processar():
        nonlocal atualizadas

        for materia_data in dados['materias']:
            for jogo_data in materia_data['jogos']:
                jogo = (
                    Disciplina.objects
                    .filter(slug=jogo_data['slug'])
                    .first()
                )

                if jogo is None:
                    sem_correspondencia.append(
                        f"{jogo_data['slug']}:jogo"
                    )
                    continue

                for modulo_data in sorted(
                    jogo_data['modulos'],
                    key=lambda item: item['ordem'],
                ):
                    modulo = (
                        jogo.modulos
                        .filter(ordem=modulo_data['ordem'])
                        .order_by('id')
                        .first()
                    )

                    if modulo is None:
                        sem_correspondencia.append(
                            (
                                f"{jogo_data['slug']}:"
                                f"módulo:{modulo_data['ordem']}"
                            )
                        )
                        continue

                    for fase_data in sorted(
                        modulo_data['fases'],
                        key=lambda item: item['ordem'],
                    ):
                        fase = (
                            modulo.fases
                            .filter(ordem=fase_data['ordem'])
                            .order_by('id')
                            .first()
                        )

                        if fase is None:
                            sem_correspondencia.append(
                                (
                                    f"{jogo_data['slug']}:"
                                    f"módulo:{modulo.ordem}:"
                                    f"fase:{fase_data['ordem']}"
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
                            questao = None

                            if (
                                indice < len(questoes)
                                and questoes[indice].enunciado.strip()
                                == questao_data['enunciado'].strip()
                            ):
                                questao = questoes[indice]
                            else:
                                questao = next(
                                    (
                                        item
                                        for item in questoes
                                        if item.enunciado.strip()
                                        == questao_data['enunciado'].strip()
                                    ),
                                    None,
                                )

                            if questao is None:
                                sem_correspondencia.append(
                                    (
                                        f"{jogo_data['slug']}:"
                                        f"módulo:{modulo.ordem}:"
                                        f"fase:{fase.ordem}:"
                                        f"questão:{indice + 1}"
                                    )
                                )
                                continue

                            nova_explicacao = (
                                questao_data
                                .get('explicacao_erro', '')
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

    if dry_run:
        processar()
    else:
        with transaction.atomic():
            processar()

    print()
    if dry_run:
        print(
            '🧪 DRY-RUN: nenhuma explicação será alterada.'
        )

    print(
        '📖 Explicações '
        f"{'que seriam ' if dry_run else ''}atualizadas: "
        f'{atualizadas}'
    )

    if sem_correspondencia:
        print(
            '⚠️ Correspondências não encontradas: '
            + ', '.join(sem_correspondencia)
        )

    print()


def importar_catalogo(
    dados,
    autor,
    replace=False,
    dry_run=False,
):
    if dry_run:
        print('🧪 DRY-RUN: nenhuma alteração será feita.')
        return

    def sincronizar_questao(fase, questao_data):
        enunciado = questao_data['enunciado'].strip()

        questao = (
            fase.questoes
            .filter(enunciado=enunciado)
            .order_by('id')
            .first()
        )

        if questao is None:
            questao = Questao.objects.create(
                fase=fase,
                enunciado=enunciado,
                explicacao_erro=questao_data.get(
                    'explicacao_erro',
                    '',
                ).strip(),
            )
            print(
                f'      + Questão criada: {enunciado[:70]}'
            )
        else:
            nova_explicacao = questao_data.get(
                'explicacao_erro',
                '',
            ).strip()

            campos_alterados = []

            if questao.explicacao_erro != nova_explicacao:
                questao.explicacao_erro = nova_explicacao
                campos_alterados.append(
                    'explicacao_erro'
                )

            if campos_alterados:
                questao.save(
                    update_fields=campos_alterados
                )

        opcoes_existentes = list(
            questao.opcoes
            .order_by('ordem', 'id')
        )

        for indice, opcao_data in enumerate(
            questao_data['opcoes'],
            start=1,
        ):
            ordem = opcao_data.get(
                'ordem',
                indice,
            )

            opcao = next(
                (
                    item
                    for item in opcoes_existentes
                    if item.ordem == ordem
                ),
                None,
            )

            if opcao is None and indice <= len(
                opcoes_existentes
            ):
                opcao = opcoes_existentes[
                    indice - 1
                ]

            if opcao is None:
                opcao = Opcao.objects.create(
                    questao=questao,
                    texto=opcao_data[
                        'texto'
                    ].strip(),
                    e_correta=opcao_data[
                        'correta'
                    ],
                    ordem=ordem,
                )
            else:
                opcao.texto = opcao_data[
                    'texto'
                ].strip()

                opcao.e_correta = opcao_data[
                    'correta'
                ]

                opcao.ordem = ordem

                opcao.save(
                    update_fields=[
                        'texto',
                        'e_correta',
                        'ordem',
                    ]
                )

    def sincronizar():
        for materia_data in sorted(
            dados['materias'],
            key=lambda item: item['ordem'],
        ):
            materia, _ = Materia.objects.update_or_create(
                slug=materia_data['slug'],
                defaults={
                    'nome': materia_data['nome'].strip(),
                    'descricao': materia_data.get(
                        'descricao',
                        '',
                    ).strip(),
                    'icone': materia_data.get(
                        'icone',
                        'book',
                    ),
                    'ordem': materia_data.get(
                        'ordem',
                        1,
                    ),
                    'ativo': materia_data.get(
                        'ativo',
                        True,
                    ),
                },
            )

            print(
                f'📚 Matéria: {materia.nome}'
            )

            for jogo_data in sorted(
                materia_data['jogos'],
                key=lambda item: item['ordem'],
            ):
                existente = (
                    Disciplina.objects
                    .filter(
                        slug=jogo_data['slug']
                    )
                    .first()
                )

                if existente and replace:
                    existente.delete()
                    existente = None

                if existente is None:
                    jogo = Disciplina.objects.create(
                        materia=materia,
                        autor=autor,
                        nome=jogo_data['nome'].strip(),
                        slug=jogo_data['slug'],
                        descricao=jogo_data.get(
                            'descricao',
                            '',
                        ).strip(),
                        icone=jogo_data.get(
                            'icone',
                            'book',
                        ),
                        ordem=jogo_data.get(
                            'ordem',
                            1,
                        ),
                        ativo=jogo_data.get(
                            'ativo',
                            True,
                        ),
                        tema=jogo_data.get(
                            'tema',
                            'tema-padrao',
                        ),
                    )
                    print(
                        f'   🎮 Jogo criado: {jogo.nome}'
                    )
                else:
                    jogo = existente
                    jogo.materia = materia
                    jogo.autor = autor
                    jogo.nome = jogo_data['nome'].strip()
                    jogo.descricao = jogo_data.get(
                        'descricao',
                        '',
                    ).strip()
                    jogo.icone = jogo_data.get(
                        'icone',
                        'book',
                    )
                    jogo.ordem = jogo_data.get(
                        'ordem',
                        1,
                    )
                    jogo.ativo = jogo_data.get(
                        'ativo',
                        True,
                    )
                    jogo.tema = jogo_data.get(
                        'tema',
                        'tema-padrao',
                    )
                    jogo.save()

                    print(
                        f'   ↻ Jogo atualizado: {jogo.nome}'
                    )

                for modulo_data in sorted(
                    jogo_data['modulos'],
                    key=lambda item: item['ordem'],
                ):
                    modulo, _ = Modulo.objects.update_or_create(
                        disciplina=jogo,
                        ordem=modulo_data['ordem'],
                        defaults={
                            'titulo': modulo_data['titulo'].strip(),
                            'descricao': modulo_data.get(
                                'descricao',
                                '',
                            ).strip(),
                        },
                    )

                    print(
                        f'      📦 Módulo {modulo.ordem}: '
                        f'{modulo.titulo}'
                    )

                    for fase_data in sorted(
                        modulo_data['fases'],
                        key=lambda item: item['ordem'],
                    ):
                        fase, _ = Fase.objects.update_or_create(
                            modulo=modulo,
                            ordem=fase_data['ordem'],
                            defaults={
                                'titulo': fase_data['titulo'].strip(),
                                'tipo': fase_data.get(
                                    'tipo',
                                    'quiz',
                                ),
                                'xp_recompensa': fase_data.get(
                                    'xp_recompensa',
                                    50,
                                ),
                                'moedas_recompensa': fase_data.get(
                                    'moedas_recompensa',
                                    10,
                                ),
                                'deslocamento_y': fase_data.get(
                                    'deslocamento_y',
                                    0,
                                ),
                            },
                        )

                        for questao_data in fase_data[
                            'questoes'
                        ]:
                            sincronizar_questao(
                                fase,
                                questao_data,
                            )

    with transaction.atomic():
        sincronizar()

    print()
    print('🎉 CATÁLOGO SINCRONIZADO COM SUCESSO!')
    print()

def criar_parser():
    parser = argparse.ArgumentParser(
        description=(
            'Importa um catálogo de matérias e jogos '
            'do Ensino Médio para o Trilha Ensino.'
        )
    )

    parser.add_argument(
        'arquivo',
        nargs='?',
        default=ARQUIVO_PADRAO,
        help=f'JSON do catálogo. Padrão: {ARQUIVO_PADRAO}',
    )

    parser.add_argument(
        '--autor',
        default='vilel',
        help='Username que será autor dos jogos.',
    )

    parser.add_argument(
        '--replace',
        action='store_true',
        help='Apaga e recria jogos existentes com o mesmo slug.',
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Valida o JSON sem alterar o banco.',
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


def main():
    parser = criar_parser()
    args = parser.parse_args()

    dados = carregar_json(args.arquivo)
    validar_catalogo(dados)

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

    if args.dry_run:
        importar_catalogo(
            dados=dados,
            autor=None,
            replace=args.replace,
            dry_run=True,
        )
        return

    autor = obter_autor(args.autor)

    importar_catalogo(
        dados=dados,
        autor=autor,
        replace=args.replace,
        dry_run=False,
    )


if __name__ == '__main__':
    main()
