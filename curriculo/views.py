import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .forms import CadastroUsuarioForm, DisciplinaForm
from .models import (
    Disciplina,
    Fase,
    Modulo,
    Opcao,
    Questao,
)

from gamificacao.models import (
    PerfilUsuario,
    ProgressoFase,
    ProgressoModulo,
    TentativaFase,
    RespostaTentativa,
)


APROVEITAMENTO_MINIMO = 0.60

DESLOCAMENTO_MINIMO = -150

DESLOCAMENTO_MAXIMO = 150

SESSAO_MODO_TESTE = 'modo_teste'


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_perfil(usuario):
    """
    Obtém ou cria o perfil do usuário.

    Isso protege usuários antigos que possam ter sido criados
    antes da existência automática do PerfilUsuario.
    """

    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=usuario
    )

    return perfil


def modo_teste_disponivel_usuario(usuario):
    """Indica se o usuário pode usar a alternância de papéis de desenvolvimento."""
    return bool(
        getattr(settings, 'DEBUG', False)
        and (usuario.is_staff or usuario.is_superuser)
    )


def papel_oficial(usuario):
    """
    Retorna o papel REAL registrado no banco.
    """

    perfil = obter_perfil(usuario)

    return perfil.tipo


def papel_efetivo(request):
    """
    Retorna o papel utilizado pela interface neste momento.

    Regra:

    1. Em produção:
       usa exclusivamente o PerfilUsuario.

    2. Durante desenvolvimento:
       pode utilizar temporariamente o modo de teste
       armazenado na sessão.

    Isso permite testar aluno/professor com um único usuário
    sem transformar a sessão na fonte oficial de autorização.
    """

    perfil = obter_perfil(
        request.user
    )

    papel_teste = request.session.get(
        SESSAO_MODO_TESTE
    )

    if (
        modo_teste_disponivel_usuario(request.user)
        and papel_teste in (
            'aluno',
            'professor',
        )
    ):

        return papel_teste

    return perfil.tipo


def modo_teste_ativo(request):
    """
    Informa se o usuário está utilizando o modo temporário
    de teste.
    """

    return (
        modo_teste_disponivel_usuario(request.user)
        and SESSAO_MODO_TESTE in request.session
    )


def usuario_e_professor(request):
    """
    Verifica o papel EFETIVO do usuário.
    """

    return (
        papel_efetivo(request)
        == 'professor'
    )


def usuario_e_aluno(request):
    """
    Verifica o papel EFETIVO do usuário.
    """

    return (
        papel_efetivo(request)
        == 'aluno'
    )


def fases_da_trilha(trilha):

    return list(
        Fase.objects
        .filter(
            modulo__disciplina=trilha
        )
        .select_related(
            'modulo'
        )
        .order_by(
            'modulo__ordem',
            'ordem',
            'id',
        )
    )


def preparar_geometria(fases):

    for indice, fase in enumerate(fases):

        fase.svg_y1 = (
            100
            + fase.deslocamento_y
        )

        if indice < len(fases) - 1:

            proxima = (
                fases[indice + 1]
            )

            fase.svg_y2 = (
                100
                + proxima.deslocamento_y
            )

        else:

            fase.svg_y2 = 100


def preparar_progressao_modulos(
    perfil,
    modulos,
):
    """
    Calcula o estado da jornada do aluno.

    A progressão possui dois níveis:
    - as fases avançam uma por vez dentro do módulo;
    - o próximo módulo é liberado automaticamente quando todas
      as fases do módulo anterior forem concluídas.

    O mapa atual não possui um cadeado central para módulos,
    portanto a liberação precisa ser persistida diretamente.
    """

    progressos = {
        progresso.fase_id: progresso
        for progresso in ProgressoFase.objects.filter(
            perfil=perfil,
            fase__modulo__in=modulos,
        )
    }

    progressos_modulo = {
        progresso.modulo_id: progresso
        for progresso in ProgressoModulo.objects.filter(
            perfil=perfil,
            modulo__in=modulos,
        )
    }

    agora = timezone.now()

    modulo_anterior_concluido = True
    primeiro_modulo = True

    for modulo in modulos:
        fases = list(
            modulo.fases.all()
        )

        modulo.total_fases = len(
            fases
        )

        modulo.fases_concluidas = sum(
            1
            for fase in fases
            if (
                progressos.get(fase.id)
                and progressos[fase.id].concluida
            )
        )

        modulo.percentual_progresso = (
            round(
                (
                    modulo.fases_concluidas
                    / modulo.total_fases
                )
                * 100
            )
            if modulo.total_fases
            else 0
        )

        modulo.concluido = (
            modulo.total_fases > 0
            and modulo.fases_concluidas
            == modulo.total_fases
        )

        progresso_modulo = (
            progressos_modulo.get(
                modulo.id
            )
        )

        if progresso_modulo is None:
            progresso_modulo = (
                ProgressoModulo.objects.create(
                    perfil=perfil,
                    modulo=modulo,
                    desbloqueado=(
                        primeiro_modulo
                        or modulo_anterior_concluido
                    ),
                    concluido=False,
                    data_desbloqueio=(
                        agora
                        if primeiro_modulo
                        or modulo_anterior_concluido
                        else None
                    ),
                )
            )

            progressos_modulo[
                modulo.id
            ] = progresso_modulo

        else:
            atualizacoes = []

            deve_desbloquear = (
                primeiro_modulo
                or modulo_anterior_concluido
            )

            if (
                deve_desbloquear
                and not progresso_modulo.desbloqueado
            ):
                progresso_modulo.desbloqueado = True
                progresso_modulo.data_desbloqueio = (
                    progresso_modulo.data_desbloqueio
                    or agora
                )
                atualizacoes.extend([
                    'desbloqueado',
                    'data_desbloqueio',
                ])

            if atualizacoes:
                progresso_modulo.save(
                    update_fields=(
                        list(
                            dict.fromkeys(
                                atualizacoes
                            )
                        )
                    )
                )

        modulo.desbloqueado = bool(
            progresso_modulo.desbloqueado
        )

        modulo.data_desbloqueio = (
            progresso_modulo.data_desbloqueio
        )

        if modulo.concluido:
            if not progresso_modulo.concluido:
                progresso_modulo.concluido = True
                progresso_modulo.data_conclusao = (
                    progresso_modulo.data_conclusao
                    or agora
                )
                progresso_modulo.save(
                    update_fields=[
                        'concluido',
                        'data_conclusao',
                    ]
                )

            modulo.status = 'concluido'

        elif modulo.desbloqueado:
            modulo.status = 'atual'

        else:
            modulo.status = 'bloqueado'

        encontrou_fase_atual = False

        for fase in fases:
            progresso = progressos.get(
                fase.id
            )

            if (
                progresso
                and progresso.concluida
            ):
                fase.status = 'concluida'

            elif (
                modulo.status == 'atual'
                and not encontrou_fase_atual
            ):
                fase.status = 'atual'
                encontrou_fase_atual = True

            else:
                fase.status = 'bloqueada'

            fase.modulo_status = modulo.status

        modulo_anterior_concluido = (
            modulo.concluido
        )

        primeiro_modulo = False

    return modulos


def modulos_da_trilha(trilha):
    return list(
        Modulo.objects
        .filter(
            disciplina=trilha,
        )
        .prefetch_related(
            'fases__questoes',
        )
        .order_by(
            'ordem',
            'id',
        )
    )


def modulo_esta_desbloqueado(
    perfil,
    modulo,
):
    """
    Confere o estado persistido do módulo.

    O primeiro módulo é sempre liberado. Os demais dependem
    do ProgressoModulo persistido após a conclusão do módulo
    anterior. A liberação é automática, sem chave manual.
    """

    primeira_ordem = (
        Modulo.objects
        .filter(
            disciplina=modulo.disciplina,
        )
        .order_by(
            'ordem',
            'id',
        )
        .values_list(
            'id',
            flat=True,
        )
        .first()
    )

    if primeira_ordem == modulo.id:
        return True

    progresso_modulo = (
        ProgressoModulo.objects
        .filter(
            perfil=perfil,
            modulo=modulo,
        )
        .first()
    )

    return bool(
        progresso_modulo
        and progresso_modulo.desbloqueado
    )


def proximo_modulo_da_trilha(
    modulo,
):
    modulos = list(
        Modulo.objects
        .filter(
            disciplina=modulo.disciplina,
        )
        .order_by(
            'ordem',
            'id',
        )
    )

    for indice, modulo_atual in enumerate(modulos):
        if modulo_atual.id == modulo.id:
            if indice + 1 < len(modulos):
                return modulos[indice + 1]

            return None

    return None


def modulo_esta_completo_para_aluno(
    perfil,
    modulo,
):
    fases = list(
        modulo.fases.all()
    )

    if not fases:
        return False

    fases_concluidas = (
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase__in=fases,
            concluida=True,
        )
        .count()
    )

    return fases_concluidas == len(fases)


def desbloquear_proximo_modulo(
    perfil,
    modulo,
    agora=None,
):
    """
    Após a conclusão total de um módulo, libera automaticamente
    o próximo módulo da jornada.

    A antiga mecânica de chave/cadeado central foi removida da
    interface, então a liberação agora acontece nesta etapa.
    """

    agora = agora or timezone.now()

    if not modulo_esta_completo_para_aluno(
        perfil,
        modulo,
    ):
        return None

    progresso_modulo, _ = (
        ProgressoModulo.objects.get_or_create(
            perfil=perfil,
            modulo=modulo,
        )
    )

    atualizacoes = []

    if not progresso_modulo.concluido:
        progresso_modulo.concluido = True
        progresso_modulo.data_conclusao = (
            progresso_modulo.data_conclusao
            or agora
        )
        atualizacoes.extend([
            'concluido',
            'data_conclusao',
        ])

    if not progresso_modulo.desbloqueado:
        progresso_modulo.desbloqueado = True
        progresso_modulo.data_desbloqueio = (
            progresso_modulo.data_desbloqueio
            or agora
        )
        atualizacoes.extend([
            'desbloqueado',
            'data_desbloqueio',
        ])

    if atualizacoes:
        progresso_modulo.save(
            update_fields=(
                list(
                    dict.fromkeys(
                        atualizacoes
                    )
                )
            )
        )

    proximo_modulo = proximo_modulo_da_trilha(
        modulo
    )

    if proximo_modulo is not None:
        proximo_progresso, criado = (
            ProgressoModulo.objects.get_or_create(
                perfil=perfil,
                modulo=proximo_modulo,
            )
        )

        if (
            not proximo_progresso.desbloqueado
        ):
            proximo_progresso.desbloqueado = True
            proximo_progresso.data_desbloqueio = (
                proximo_progresso.data_desbloqueio
                or agora
            )
            proximo_progresso.save(
                update_fields=[
                    'desbloqueado',
                    'data_desbloqueio',
                ]
            )

    return proximo_modulo


def fase_esta_liberada(
    request,
    fase,
):
    """
    Verifica no servidor se a fase pode ser executada pelo aluno.

    A fase precisa pertencer a um módulo desbloqueado e todas
    as fases anteriores do mesmo módulo precisam estar concluídas.
    Professores continuam com acesso de visualização a qualquer
    fase da própria trilha.
    """

    trilha = fase.modulo.disciplina
    papel = papel_efetivo(request)

    if papel == 'professor':
        return trilha.autor_id == request.user.id

    if not trilha.ativo:
        return False

    perfil = obter_perfil(
        request.user
    )

    if not modulo_esta_desbloqueado(
        perfil,
        fase.modulo,
    ):
        return False

    fases_concluidas = set(
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase__modulo__disciplina=trilha,
            concluida=True,
        )
        .values_list(
            'fase_id',
            flat=True,
        )
    )

    for fase_anterior in (
        fase.modulo.fases
        .all()
        .order_by(
            'ordem',
            'id',
        )
    ):
        if fase_anterior.id == fase.id:
            return True

        if fase_anterior.id not in fases_concluidas:
            return False

    return False

def trilha_acessivel_para_usuario(
    request,
    trilha_id,
):

    papel = papel_efetivo(
        request
    )

    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    if papel == 'professor':

        return get_object_or_404(
            Disciplina,
            id=trilha_id,
            autor=request.user,
        )

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    return get_object_or_404(
        Disciplina,
        id=trilha_id,
        ativo=True,
    )


def contexto_papel(request):

    perfil = obter_perfil(
        request.user
    )

    papel = papel_efetivo(
        request
    )

    return {
        'perfil': perfil,
        'papel_oficial': perfil.tipo,
        'papel_efetivo': papel,
        'modo_teste_ativo': modo_teste_ativo(request),
        'modo_teste_disponivel': modo_teste_disponivel_usuario(request.user),
    }


# ============================================================
# 1. ROTEAMENTO
# ============================================================

@login_required
def redirecionamento_inicial(request):

    papel = papel_efetivo(
        request
    )

    if papel == 'professor':

        return redirect(
            'dashboard_professor'
        )

    return redirect(
        'dashboard_aluno'
    )


@login_required
def alternar_papel(request):
    """
    Alterna ALUNO <-> PROFESSOR somente para testes locais.

    O papel oficial gravado em PerfilUsuario nunca é alterado.
    A alternância só funciona em DEBUG e para usuários de equipe
    (staff/superuser), evitando transformar uma conta comum em
    professor por uma rota pública.
    """

    if request.method != 'POST':
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Método não permitido. Use POST.',
            },
            status=405,
        )

    if not modo_teste_disponivel_usuario(request.user):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Modo de teste indisponível para esta conta.',
            },
            status=403,
        )

    papel_atual = papel_efetivo(request)
    novo_papel = 'aluno' if papel_atual == 'professor' else 'professor'

    request.session[SESSAO_MODO_TESTE] = novo_papel
    request.session.modified = True

    return redirect('redirecionamento_inicial')


# ============================================================
# 2. CADASTRO DE USUÁRIO
# ============================================================


def cadastro_usuario(request):
    """Cria uma conta pública sempre como aluno."""

    if request.user.is_authenticated:
        return redirect('redirecionamento_inicial')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)

        if form.is_valid():
            usuario = form.save()

            # O sinal post_save cria o PerfilUsuario automaticamente.
            # Mantemos explicitamente o papel de aluno para deixar a
            # regra do cadastro público clara e determinística.
            perfil = obter_perfil(usuario)
            if perfil.tipo != 'aluno':
                perfil.tipo = 'aluno'
                perfil.save(update_fields=['tipo'])

            login(request, usuario)
            return redirect('redirecionamento_inicial')
    else:
        form = CadastroUsuarioForm()

    return render(
        request,
        'registration/cadastro.html',
        {'form': form},
    )


# ============================================================
# 2. DASHBOARD DO ALUNO
# ============================================================

@login_required
def dashboard_aluno(request):

    papel = papel_efetivo(
        request
    )

    if papel == 'professor':

        return redirect(
            'dashboard_professor'
        )

    perfil = obter_perfil(
        request.user
    )

    trilhas = list(
        Disciplina.objects
        .filter(
            ativo=True
        )
        .select_related(
            'autor'
        )
        .prefetch_related(
            'modulos__fases'
        )
        .order_by(
            'ordem',
            'nome',
        )
    )

    # --------------------------------------------------------
    # Uma consulta para obter as fases concluídas
    # --------------------------------------------------------

    fases_concluidas_ids = set(
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            concluida=True,
        )
        .values_list(
            'fase_id',
            flat=True,
        )
    )

    # --------------------------------------------------------
    # Progresso de cada trilha
    # --------------------------------------------------------

    for trilha in trilhas:

        fases = []

        for modulo in (
            trilha.modulos.all()
        ):

            fases.extend(
                modulo.fases.all()
            )

        total_fases = len(
            fases
        )

        fases_concluidas = sum(
            fase.id
            in fases_concluidas_ids
            for fase in fases
        )

        if total_fases > 0:

            percentual = round(
                (
                    fases_concluidas
                    / total_fases
                )
                * 100
            )

        else:

            percentual = 0

        trilha.total_fases = (
            total_fases
        )

        trilha.fases_concluidas = (
            fases_concluidas
        )

        trilha.percentual_progresso = (
            percentual
        )

        trilha.concluida = (
            total_fases > 0
            and (
                fases_concluidas
                == total_fases
            )
        )

    fases_revisao = list(
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            tentativas__gt=0,
            melhor_aproveitamento__lt=Decimal('60'),
        )
        .select_related(
            'fase__modulo__disciplina'
        )
        .order_by(
            'melhor_aproveitamento',
            '-data_ultima_tentativa',
        )[:6]
    )

    contexto = contexto_papel(
        request
    )

    contexto.update({
        'trilhas': trilhas,
        'fases_revisao': fases_revisao,
        'dashboard_modo': 'aluno',
    })

    return render(
        request,
        'curriculo/aluno_dashboard.html',
        contexto,
    )


# ============================================================
# 3. DASHBOARD DO PROFESSOR
# ============================================================

@login_required
def dashboard_professor(request):

    papel = papel_efetivo(
        request
    )

    if papel != 'professor':

        return redirect(
            'dashboard_aluno'
        )

    minhas_trilhas = list(
        Disciplina.objects
        .filter(
            autor=request.user
        )
        .prefetch_related(
            'modulos__fases__questoes'
        )
        .order_by(
            'ordem',
            'nome',
        )
    )

    for trilha in minhas_trilhas:
        trilha.total_modulos = len(
            trilha.modulos.all()
        )
        trilha.total_fases = sum(
            len(modulo.fases.all())
            for modulo in trilha.modulos.all()
        )
        trilha.total_questoes = sum(
            len(fase.questoes.all())
            for modulo in trilha.modulos.all()
            for fase in modulo.fases.all()
        )

    contexto = contexto_papel(
        request
    )

    total_modulos = sum(
        trilha.total_modulos
        for trilha in minhas_trilhas
    )
    total_fases = sum(
        trilha.total_fases
        for trilha in minhas_trilhas
    )
    total_questoes = sum(
        trilha.total_questoes
        for trilha in minhas_trilhas
    )
    total_publicadas = sum(
        trilha.ativo
        for trilha in minhas_trilhas
    )

    contexto.update({
        'trilhas': minhas_trilhas,
        'total_trilhas': len(minhas_trilhas),
        'total_publicadas': total_publicadas,
        'total_modulos': total_modulos,
        'total_fases': total_fases,
        'total_questoes': total_questoes,
        'dashboard_modo': 'professor',
    })

    return render(
        request,
        'curriculo/professor_dashboard.html',
        contexto,
    )


# ============================================================
# 4. CRIAÇÃO DE TRILHA
# ============================================================

@login_required
def criar_trilha(request):

    if not usuario_e_professor(
        request
    ):

        return redirect(
            'dashboard_aluno'
        )

    if request.method == 'POST':

        form = DisciplinaForm(
            request.POST
        )

        if form.is_valid():

            trilha = form.save(
                commit=False
            )

            trilha.autor = (
                request.user
            )

            trilha.ativo = False

            trilha.save()

            return redirect(
                'dashboard_professor'
            )

    else:

        form = DisciplinaForm()

    return render(
        request,
        'curriculo/criar_trilha.html',
        {
            'form': form,
            'perfil': obter_perfil(request.user),
            'tema_aplicado': form.data.get('tema', form.initial.get('tema', 'tema-padrao')) or 'tema-padrao',
        },
    )


# ============================================================
# 5. EXCLUSÃO DE TRILHA
# ============================================================

@login_required
def deletar_trilha(
    request,
    trilha_id,
):

    if not usuario_e_professor(
        request
    ):

        return redirect(
            'dashboard_aluno'
        )

    trilha = get_object_or_404(
        Disciplina,
        id=trilha_id,
        autor=request.user,
    )

    if request.method == 'POST':

        trilha.delete()

    return redirect(
        'dashboard_professor'
    )


# ============================================================
# 6. PUBLICAÇÃO DA TRILHA
# ============================================================

@login_required
def alternar_publicacao(request, trilha_id):

    if not usuario_e_professor(request):
        return redirect('dashboard_aluno')

    if request.method != 'POST':
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Método não permitido.',
            },
            status=405,
        )

    trilha = get_object_or_404(
        Disciplina,
        id=trilha_id,
        autor=request.user,
    )

    total_fases = Fase.objects.filter(
        modulo__disciplina=trilha
    ).count()

    total_questoes = Questao.objects.filter(
        fase__modulo__disciplina=trilha
    ).count()

    if (
        not trilha.ativo
        and (
            total_fases == 0
            or total_questoes == 0
        )
    ):
        messages.error(
            request,
            'Antes de publicar, cadastre pelo menos uma fase e uma questão.',
        )
        return redirect(
            'editar_trilha',
            trilha_id=trilha.id,
        )

    trilha.ativo = not trilha.ativo

    trilha.save(
        update_fields=['ativo']
    )

    messages.success(
        request,
        (
            'Trilha publicada para os alunos.'
            if trilha.ativo
            else 'Trilha voltou para rascunho.'
        ),
    )

    return redirect('dashboard_professor')


# ============================================================
# 6. EDITOR DA TRILHA
# ============================================================

@login_required
def editar_trilha(
    request,
    trilha_id,
):

    if not usuario_e_professor(
        request
    ):

        return redirect(
            'dashboard_aluno'
        )

    trilha = get_object_or_404(
        Disciplina,
        id=trilha_id,
        autor=request.user,
    )

    modulos = list(
        Modulo.objects
        .filter(
            disciplina=trilha
        )
        .prefetch_related(
            'fases__questoes',
        )
        .order_by(
            'ordem',
            'id',
        )
    )

    fases = fases_da_trilha(
        trilha
    )

    preparar_geometria(
        fases
    )

    fases_por_modulo = []

    for modulo in modulos:
        fases_modulo = list(
            modulo.fases.all()
        )

        fases_por_modulo.append(
            fases_modulo
        )

    # As fases do editor vêm do prefetch de cada módulo e são
    # instâncias diferentes das fases usadas por fases_da_trilha().
    # A geometria precisa ser preparada nessas mesmas instâncias
    # que serão renderizadas no mapa do editor.
    fases_editor = [
        fase
        for fases_modulo in fases_por_modulo
        for fase in fases_modulo
    ]

    preparar_geometria(
        fases_editor
    )

    for indice, modulo in enumerate(modulos[:-1]):

        fases_atual = fases_por_modulo[indice]
        fases_seguinte = fases_por_modulo[indice + 1]

        modulo.transicao_svg_y1 = (
            fases_atual[-1].svg_y1
            if fases_atual
            else 100
        )

        modulo.transicao_svg_y2 = (
            fases_seguinte[0].svg_y1
            if fases_seguinte
            else 100
        )

    total_questoes = sum(
        fase.questoes.count()
        for fase in fases
    )

    modulo_anterior_id = None

    for fase in fases:
        fase.primeira_do_modulo = (
            fase.modulo_id != modulo_anterior_id
        )

        if fase.primeira_do_modulo:
            modulo_anterior_id = fase.modulo_id

    return render(
        request,
        'curriculo/editar_trilha.html',
        {
            'trilha': trilha,
            'modulos': modulos,
            'fases': fases,
            'visualizacao_professor': True,
            'total_questoes': total_questoes,
            'perfil': obter_perfil(request.user),
            'tema_aplicado': trilha.tema,
        },
    )


# ============================================================
# 7. ATUALIZAR POSIÇÃO DA FASE
# ============================================================

@login_required
def atualizar_y_fase(
    request,
    fase_id,
):

    if not usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Acesso permitido '
                    'apenas a professores.'
                ),
            },
            status=403,
        )

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    fase = get_object_or_404(
        Fase,
        id=fase_id,
        modulo__disciplina__autor=request.user,
    )

    try:

        data = json.loads(
            request.body or '{}'
        )

        deslocamento = int(
            data.get(
                'y',
                0,
            )
        )

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Valor de deslocamento inválido.'
                ),
            },
            status=400,
        )

    deslocamento = max(
        DESLOCAMENTO_MINIMO,
        min(
            DESLOCAMENTO_MAXIMO,
            deslocamento,
        ),
    )

    fase.deslocamento_y = (
        deslocamento
    )

    fase.save(
        update_fields=[
            'deslocamento_y'
        ]
    )

    return JsonResponse(
        {
            'status': 'ok',
            'deslocamento_y': (
                deslocamento
            ),
        }
    )


# ============================================================
# 8. ATUALIZAR TEMA
# ============================================================

@login_required
def ajax_atualizar_tema(
    request,
    trilha_id,
):

    if not usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Acesso permitido '
                    'apenas a professores.'
                ),
            },
            status=403,
        )

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    trilha = get_object_or_404(
        Disciplina,
        id=trilha_id,
        autor=request.user,
    )

    try:

        data = json.loads(
            request.body or '{}'
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'JSON inválido.',
            },
            status=400,
        )

    novo_tema = data.get(
        'tema',
        'tema-padrao',
    )

    temas_validos = {
        valor
        for valor, _ in Disciplina.TEMAS
    }

    if novo_tema not in temas_validos:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Tema inválido.',
            },
            status=400,
        )

    trilha.tema = novo_tema

    trilha.save(
        update_fields=[
            'tema'
        ]
    )

    return JsonResponse(
        {
            'status': 'ok',
            'tema': novo_tema,
        }
    )


# ============================================================
# 9. CRIAÇÃO DE MÓDULO
# ============================================================

@login_required
def ajax_criar_modulo(
    request,
    trilha_id,
):

    if not usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Acesso permitido '
                    'apenas a professores.'
                ),
            },
            status=403,
        )

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    trilha = get_object_or_404(
        Disciplina,
        id=trilha_id,
        autor=request.user,
    )

    titulo = request.POST.get(
        'titulo',
        '',
    ).strip()

    descricao = request.POST.get(
        'descricao',
        '',
    ).strip()

    try:

        ordem = int(
            request.POST.get(
                'ordem',
                1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        ordem = 1

    if not titulo:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Informe o título do módulo.'
                ),
            },
            status=400,
        )

    if ordem < 1:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'A ordem deve ser maior '
                    'ou igual a 1.'
                ),
            },
            status=400,
        )

    modulo = Modulo.objects.create(
        disciplina=trilha,
        titulo=titulo,
        descricao=descricao,
        ordem=ordem,
    )

    return JsonResponse(
        {
            'status': 'ok',
            'modulo': {
                'id': modulo.id,
                'titulo': modulo.titulo,
                'descricao': modulo.descricao,
                'ordem': modulo.ordem,
            },
        }
    )


# ============================================================
# 10. CRIAÇÃO DE FASE
# ============================================================

@login_required
def ajax_criar_fase(
    request,
    trilha_id,
):

    if not usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Acesso permitido '
                    'apenas a professores.'
                ),
            },
            status=403,
        )

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    modulo_id = request.POST.get(
        'modulo_id'
    )

    titulo = request.POST.get(
        'titulo',
        '',
    ).strip()

    if not modulo_id:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Selecione um módulo.'
                ),
            },
            status=400,
        )

    try:

        ordem = int(
            request.POST.get(
                'ordem',
                1,
            )
        )

        xp_recompensa = int(
            request.POST.get(
                'xp_recompensa',
                50,
            )
        )

        moedas_recompensa = int(
            request.POST.get(
                'moedas_recompensa',
                10,
            )
        )

        deslocamento_y = int(
            request.POST.get(
                'deslocamento_y',
                0,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Um dos valores '
                    'numéricos é inválido.'
                ),
            },
            status=400,
        )

    modulo = get_object_or_404(
        Modulo,
        id=modulo_id,
        disciplina__id=trilha_id,
        disciplina__autor=request.user,
    )

    tipo = request.POST.get(
        'tipo',
        'quiz',
    )

    tipos_validos = {
        valor
        for valor, _
        in Fase.TIPO_CHOICES
    }

    if not titulo:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Informe o título da fase.'
                ),
            },
            status=400,
        )

    if ordem < 1:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'A ordem deve ser maior '
                    'ou igual a 1.'
                ),
            },
            status=400,
        )

    if xp_recompensa < 0:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'O XP não pode ser negativo.'
                ),
            },
            status=400,
        )

    if moedas_recompensa < 0:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'As moedas não podem '
                    'ser negativas.'
                ),
            },
            status=400,
        )

    if tipo not in tipos_validos:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Tipo de fase inválido.'
                ),
            },
            status=400,
        )

    deslocamento_y = max(
        DESLOCAMENTO_MINIMO,
        min(
            DESLOCAMENTO_MAXIMO,
            deslocamento_y,
        ),
    )

    fase = Fase.objects.create(
        modulo=modulo,
        titulo=titulo,
        ordem=ordem,
        tipo=tipo,
        xp_recompensa=xp_recompensa,
        moedas_recompensa=moedas_recompensa,
        deslocamento_y=deslocamento_y,
    )

    return JsonResponse(
        {
            'status': 'ok',
            'fase': {
                'id': fase.id,
                'titulo': fase.titulo,
                'ordem': fase.ordem,
            },
        }
    )


# ============================================================
# 11. EDIÇÃO E EXCLUSÃO DE CONTEÚDO
# ============================================================

@login_required
def ajax_editar_modulo(request, modulo_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {'status': 'erro', 'msg': 'Acesso permitido apenas a professores.'},
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {'status': 'erro', 'msg': 'Método não permitido.'},
            status=405,
        )

    modulo = get_object_or_404(
        Modulo,
        id=modulo_id,
        disciplina__autor=request.user,
    )

    titulo = request.POST.get('titulo', '').strip()
    descricao = request.POST.get('descricao', '').strip()

    try:
        ordem = int(request.POST.get('ordem', modulo.ordem))
    except (TypeError, ValueError):
        return JsonResponse(
            {'status': 'erro', 'msg': 'A ordem do módulo é inválida.'},
            status=400,
        )

    if not titulo:
        return JsonResponse(
            {'status': 'erro', 'msg': 'Informe o título do módulo.'},
            status=400,
        )

    if ordem < 1:
        return JsonResponse(
            {'status': 'erro', 'msg': 'A ordem deve ser maior ou igual a 1.'},
            status=400,
        )

    modulo.titulo = titulo
    modulo.descricao = descricao
    modulo.ordem = ordem
    modulo.save(update_fields=['titulo', 'descricao', 'ordem'])

    return JsonResponse(
        {
            'status': 'ok',
            'modulo': {
                'id': modulo.id,
                'titulo': modulo.titulo,
                'descricao': modulo.descricao,
                'ordem': modulo.ordem,
            },
        }
    )


@login_required
def ajax_editar_fase(request, fase_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {'status': 'erro', 'msg': 'Acesso permitido apenas a professores.'},
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {'status': 'erro', 'msg': 'Método não permitido.'},
            status=405,
        )

    fase = get_object_or_404(
        Fase,
        id=fase_id,
        modulo__disciplina__autor=request.user,
    )

    modulo_id = request.POST.get('modulo_id')
    titulo = request.POST.get('titulo', '').strip()
    tipo = request.POST.get('tipo', fase.tipo)

    try:
        ordem = int(request.POST.get('ordem', fase.ordem))
        xp_recompensa = int(request.POST.get('xp_recompensa', fase.xp_recompensa))
        moedas_recompensa = int(request.POST.get('moedas_recompensa', fase.moedas_recompensa))
        deslocamento_y = int(request.POST.get('deslocamento_y', fase.deslocamento_y))
    except (TypeError, ValueError):
        return JsonResponse(
            {'status': 'erro', 'msg': 'Um dos valores numéricos é inválido.'},
            status=400,
        )

    if not titulo:
        return JsonResponse(
            {'status': 'erro', 'msg': 'Informe o título da fase.'},
            status=400,
        )

    if ordem < 1 or xp_recompensa < 0 or moedas_recompensa < 0:
        return JsonResponse(
            {'status': 'erro', 'msg': 'Verifique ordem, XP e moedas.'},
            status=400,
        )

    tipos_validos = {valor for valor, _ in Fase.TIPO_CHOICES}
    if tipo not in tipos_validos:
        return JsonResponse(
            {'status': 'erro', 'msg': 'Tipo de fase inválido.'},
            status=400,
        )

    modulo = get_object_or_404(
        Modulo,
        id=modulo_id,
        disciplina__autor=request.user,
    )

    if modulo.disciplina_id != fase.modulo.disciplina_id:
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'A fase só pode ser movida dentro da própria trilha.',
            },
            status=400,
        )

    deslocamento_y = max(
        DESLOCAMENTO_MINIMO,
        min(DESLOCAMENTO_MAXIMO, deslocamento_y),
    )

    fase.modulo = modulo
    fase.titulo = titulo
    fase.ordem = ordem
    fase.tipo = tipo
    fase.xp_recompensa = xp_recompensa
    fase.moedas_recompensa = moedas_recompensa
    fase.deslocamento_y = deslocamento_y
    fase.save(
        update_fields=[
            'modulo',
            'titulo',
            'ordem',
            'tipo',
            'xp_recompensa',
            'moedas_recompensa',
            'deslocamento_y',
        ]
    )

    return JsonResponse(
        {
            'status': 'ok',
            'fase': {
                'id': fase.id,
                'titulo': fase.titulo,
                'ordem': fase.ordem,
                'tipo': fase.tipo,
                'xp_recompensa': fase.xp_recompensa,
                'moedas_recompensa': fase.moedas_recompensa,
                'deslocamento_y': fase.deslocamento_y,
                'modulo_id': fase.modulo_id,
            },
        }
    )


@login_required
def ajax_excluir_modulo(request, modulo_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {'status': 'erro', 'msg': 'Acesso permitido apenas a professores.'},
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {'status': 'erro', 'msg': 'Método não permitido.'},
            status=405,
        )

    modulo = get_object_or_404(
        Modulo,
        id=modulo_id,
        disciplina__autor=request.user,
    )

    modulo.delete()

    return JsonResponse({'status': 'ok'})


@login_required
def ajax_excluir_fase(request, fase_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {'status': 'erro', 'msg': 'Acesso permitido apenas a professores.'},
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {'status': 'erro', 'msg': 'Método não permitido.'},
            status=405,
        )

    fase = get_object_or_404(
        Fase,
        id=fase_id,
        modulo__disciplina__autor=request.user,
    )

    fase.delete()

    return JsonResponse({'status': 'ok'})


# ============================================================
# 12. CRIAÇÃO DE QUESTÃO
# ============================================================

@login_required
def ajax_criar_questao(
    request,
):

    if not usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Acesso permitido '
                    'apenas a professores.'
                ),
            },
            status=403,
        )

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    fase_id = request.POST.get(
        'fase_id'
    )

    if not fase_id:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Fase não informada.'
                ),
            },
            status=400,
        )

    fase = get_object_or_404(
        Fase,
        id=fase_id,
        modulo__disciplina__autor=request.user,
    )

    enunciado = request.POST.get(
        'enunciado',
        '',
    ).strip()

    explicacao = request.POST.get(
        'explicacao_erro',
        '',
    ).strip()

    correta_idx = request.POST.get(
        'op_correta'
    )

    if not enunciado:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Preencha o enunciado.'
                ),
            },
            status=400,
        )

    if correta_idx is None:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Marque a resposta correta.'
                ),
            },
            status=400,
        )

    try:

        correta_idx = int(
            correta_idx
        )

    except (
        TypeError,
        ValueError,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Alternativa correta inválida.'
                ),
            },
            status=400,
        )

    opcoes = []

    for indice in range(4):

        texto = request.POST.get(
            f'op_texto_{indice}',
            '',
        ).strip()

        if texto:

            opcoes.append(
                {
                    'indice': indice,
                    'texto': texto,
                }
            )

    if len(opcoes) < 2:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Cadastre pelo menos '
                    'duas alternativas.'
                ),
            },
            status=400,
        )

    if not any(
        opcao['indice']
        == correta_idx
        for opcao in opcoes
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'A alternativa correta '
                    'está vazia.'
                ),
            },
            status=400,
        )

    with transaction.atomic():

        questao = Questao.objects.create(
            fase=fase,
            enunciado=enunciado,
            explicacao_erro=explicacao,
        )

        for opcao in opcoes:

            Opcao.objects.create(
                questao=questao,
                texto=opcao['texto'],
                e_correta=(
                    opcao['indice']
                    == correta_idx
                ),
            )

    return JsonResponse(
        {
            'status': 'ok',
            'questao_id': questao.id,
        }
    )


# ============================================================
# 12. EDIÇÃO E EXCLUSÃO DE QUESTÃO
# ============================================================

@login_required
def ajax_editar_questao(request, questao_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Acesso permitido apenas a professores.',
            },
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Método não permitido.',
            },
            status=405,
        )

    questao = get_object_or_404(
        Questao,
        id=questao_id,
        fase__modulo__disciplina__autor=request.user,
    )

    enunciado = request.POST.get(
        'enunciado',
        '',
    ).strip()

    explicacao = request.POST.get(
        'explicacao_erro',
        '',
    ).strip()

    correta_idx = request.POST.get(
        'op_correta'
    )

    if not enunciado:
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Preencha o enunciado.',
            },
            status=400,
        )

    if correta_idx is None:
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Marque a resposta correta.',
            },
            status=400,
        )

    try:
        correta_idx = int(correta_idx)
    except (TypeError, ValueError):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Alternativa correta inválida.',
            },
            status=400,
        )

    if correta_idx not in range(4):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Alternativa correta inválida.',
            },
            status=400,
        )

    opcoes = []

    for indice in range(4):
        texto = request.POST.get(
            f'op_texto_{indice}',
            '',
        ).strip()

        if texto:
            opcoes.append(
                {
                    'indice': indice,
                    'texto': texto,
                }
            )

    if len(opcoes) < 2:
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Cadastre pelo menos duas alternativas.',
            },
            status=400,
        )

    if not any(
        opcao['indice'] == correta_idx
        for opcao in opcoes
    ):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'A alternativa correta está vazia.',
            },
            status=400,
        )

    with transaction.atomic():
        opcoes_existentes = list(
            questao.opcoes.order_by('id')
        )

        for posicao, opcao in enumerate(opcoes):
            correta = opcao['indice'] == correta_idx

            if posicao < len(opcoes_existentes):
                objeto = opcoes_existentes[posicao]
                objeto.texto = opcao['texto']
                objeto.e_correta = correta
                objeto.save(
                    update_fields=[
                        'texto',
                        'e_correta',
                    ]
                )
            else:
                Opcao.objects.create(
                    questao=questao,
                    texto=opcao['texto'],
                    e_correta=correta,
                )

        for objeto in opcoes_existentes[len(opcoes):]:
            objeto.delete()

        questao.enunciado = enunciado
        questao.explicacao_erro = explicacao
        questao.save(
            update_fields=[
                'enunciado',
                'explicacao_erro',
            ]
        )

    return JsonResponse(
        {
            'status': 'ok',
            'questao': {
                'id': questao.id,
                'fase_id': questao.fase_id,
                'enunciado': questao.enunciado,
            },
        }
    )


@login_required
def ajax_excluir_questao(request, questao_id):

    if not usuario_e_professor(request):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Acesso permitido apenas a professores.',
            },
            status=403,
        )

    if request.method != 'POST':
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Método não permitido.',
            },
            status=405,
        )

    questao = get_object_or_404(
        Questao,
        id=questao_id,
        fase__modulo__disciplina__autor=request.user,
    )

    questao.delete()

    return JsonResponse(
        {
            'status': 'ok',
        }
    )


# ============================================================
# 12. MAPA DA TRILHA
# ============================================================

@login_required
def trilha_view(
    request,
    trilha_id,
):

    perfil = obter_perfil(
        request.user
    )

    trilha = (
        trilha_acessivel_para_usuario(
            request,
            trilha_id,
        )
    )

    modulos = modulos_da_trilha(
        trilha
    )

    fases = []
    fases_por_modulo = []

    for modulo in modulos:
        fases_modulo = list(
            modulo.fases.all()
        )

        preparar_geometria(
            fases_modulo
        )

        fases_por_modulo.append(
            fases_modulo
        )

        fases.extend(
            fases_modulo
        )

    # A ligação entre módulos é uma continuação da própria trilha.
    # Sua curva usa a posição vertical da última fase do módulo atual
    # e a posição vertical da primeira fase do módulo seguinte.
    for indice, modulo in enumerate(modulos[:-1]):

        fases_atual = fases_por_modulo[indice]
        fases_seguinte = fases_por_modulo[indice + 1]

        modulo.transicao_svg_y1 = (
            fases_atual[-1].svg_y1
            if fases_atual
            else 100
        )

        modulo.transicao_svg_y2 = (
            fases_seguinte[0].svg_y1
            if fases_seguinte
            else 100
        )

    papel = papel_efetivo(
        request
    )

    modo_preview_aluno = (
        papel == 'professor'
        and request.GET.get('preview') == 'aluno'
        and trilha.autor_id == request.user.id
    )

    papel_exibicao = (
        'aluno'
        if modo_preview_aluno
        else papel
    )

    # Prévia como aluno usa a própria tela final da trilha, com uma
    # jornada inicial simulada. Ela não altera ProgressoFase/ProgressoModulo.
    if modo_preview_aluno:

        for indice, modulo in enumerate(modulos):

            fases_modulo = list(
                modulo.fases.all()
            )

            modulo.total_fases = len(
                fases_modulo
            )
            modulo.fases_concluidas = 0
            modulo.percentual_progresso = 0

            modulo.desbloqueado = (
                indice == 0
            )

            modulo.status = (
                'atual'
                if indice == 0
                else 'bloqueado'
            )

            for fase_indice, fase in enumerate(
                fases_modulo
            ):

                if indice == 0 and fase_indice == 0:
                    fase.status = 'atual'
                else:
                    fase.status = 'bloqueada'

    # Professores visualizam todo o conteúdo da própria trilha.
    elif papel == 'professor':

        for modulo in modulos:
            fases_modulo = list(
                modulo.fases.all()
            )

            modulo.total_fases = len(
                fases_modulo
            )
            modulo.fases_concluidas = 0
            modulo.percentual_progresso = 0
            modulo.status = 'professor'
            modulo.desbloqueado = True

            for fase in fases_modulo:
                fase.status = 'professor'

    else:

        preparar_progressao_modulos(
            perfil,
            modulos,
        )

    fases_concluidas = sum(
        fase.status
        == 'concluida'
        for fase in fases
    )

    total_fases = len(
        fases
    )

    if total_fases > 0:

        percentual_progresso = round(
            (
                fases_concluidas
                / total_fases
            )
            * 100
        )

    else:

        percentual_progresso = 0

    fase_atual = next(
        (
            fase
            for fase in fases
            if fase.status
            == 'atual'
        ),
        None,
    )

    modulos_concluidos = sum(
        modulo.status == 'concluido'
        for modulo in modulos
    )

    tema_aplicado = (
        perfil.tema_fundo
        if papel == 'aluno'
        else trilha.tema
    )

    contexto = contexto_papel(
        request
    )

    contexto.update({
        'trilha': trilha,
        'visualizacao_professor': (
            papel == 'professor'
            and not modo_preview_aluno
        ),
        'modo_preview_aluno': modo_preview_aluno,
        'papel_exibicao': papel_exibicao,
        'modulos': modulos,
        'modulos_concluidos': (
            modulos_concluidos
        ),
        'fases': fases,
        'fases_concluidas': (
            fases_concluidas
        ),
        'total_fases': (
            total_fases
        ),
        'percentual_progresso': (
            percentual_progresso
        ),
        'fase_atual': (
            fase_atual
        ),
        'tema_aplicado': tema_aplicado,
    })

    return render(
        request,
        'curriculo/trilha.html',
        contexto,
    )


# ============================================================
# 13. TELA DA FASE
# ============================================================

@login_required
def fase_detalhe(
    request,
    fase_id,
):

    fase = get_object_or_404(
        Fase.objects.select_related(
            'modulo__disciplina'
        ),
        id=fase_id,
    )

    if not fase_esta_liberada(
        request,
        fase,
    ):

        return redirect(
            'trilha',
            trilha_id=(
                fase.modulo.disciplina_id
            ),
        )

    perfil = obter_perfil(
        request.user
    )

    progresso = (
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase=fase,
        )
        .first()
    )

    sem_vidas = (
        usuario_e_aluno(request)
        and perfil.vidas <= 0
        and not (
            progresso
            and progresso.concluida
        )
    )

    tema_aplicado = (
        perfil.tema_fundo
        if usuario_e_aluno(request)
        else fase.modulo.disciplina.tema
    )

    questoes = []

    questoes_db = (
        fase.questoes
        .prefetch_related(
            'opcoes'
        )
        .all()
    )

    for questao in questoes_db:

        questoes.append(
            {
                'id': (
                    questao.id
                ),
                'enunciado': (
                    questao.enunciado
                ),
                'explicacao_erro': (
                    questao.explicacao_erro
                ),
                'opcoes': [
                    {
                        'id': opcao.id,
                        'texto': opcao.texto,
                    }
                    for opcao
                    in questao.opcoes.all()
                ],
            }
        )

    contexto = contexto_papel(
        request
    )

    contexto.update({
        'fase': fase,
        'questoes_json': questoes,
        'trilha_id': (
            fase.modulo.disciplina_id
        ),
        'progresso': progresso,
        'sem_vidas': sem_vidas,
        'tema_aplicado': tema_aplicado,
    })

    return render(
        request,
        'curriculo/fase_detalhe.html',
        contexto,
    )


# ============================================================
# 14. VERIFICAÇÃO DE RESPOSTA
# ============================================================

@login_required
def verificar_resposta(
    request,
    fase_id,
):

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    fase = get_object_or_404(
        Fase.objects.select_related(
            'modulo__disciplina'
        ),
        id=fase_id,
    )

    if not fase_esta_liberada(
        request,
        fase,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Esta fase ainda '
                    'está bloqueada.'
                ),
            },
            status=403,
        )

    try:

        data = json.loads(
            request.body or '{}'
        )

        questao_id = int(
            data.get(
                'questao_id'
            )
        )

        opcao_id = int(
            data.get(
                'opcao_id'
            )
        )

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Dados da resposta inválidos.'
                ),
            },
            status=400,
        )

    perfil = obter_perfil(
        request.user
    )

    progresso = (
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase=fase,
        )
        .first()
    )

    if (
        usuario_e_aluno(request)
        and perfil.vidas <= 0
        and not (
            progresso
            and progresso.concluida
        )
    ):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Você está sem vidas. '
                    'Recarregue na loja para continuar.'
                ),
            },
            status=409,
        )

    questao = get_object_or_404(
        Questao,
        id=questao_id,
        fase=fase,
    )

    opcao = get_object_or_404(
        Opcao,
        id=opcao_id,
        questao=questao,
    )

    opcao_correta_id = (
        questao.opcoes
        .filter(
            e_correta=True
        )
        .values_list(
            'id',
            flat=True,
        )
        .first()
    )

    correta = (
        opcao.id
        == opcao_correta_id
    )

    return JsonResponse(
        {
            'status': 'ok',
            'correta': correta,
            'explicacao_erro': (
                ''
                if correta
                else (
                    questao.explicacao_erro
                )
            ),
        }
    )


# ============================================================
# 15. FINALIZAÇÃO DA FASE
# ============================================================

@login_required
def finalizar_fase(
    request,
    fase_id,
):

    if request.method != 'POST':

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Método não permitido.'
                ),
            },
            status=405,
        )

    fase = get_object_or_404(
        Fase.objects.select_related(
            'modulo__disciplina'
        ),
        id=fase_id,
    )

    if not fase_esta_liberada(
        request,
        fase,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Esta fase ainda '
                    'está bloqueada.'
                ),
            },
            status=403,
        )

    perfil = obter_perfil(
        request.user
    )

    progresso_existente = (
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase=fase,
        )
        .first()
    )

    if (
        usuario_e_aluno(request)
        and perfil.vidas <= 0
        and not (
            progresso_existente
            and progresso_existente.concluida
        )
    ):
        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Você está sem vidas. '
                    'Recarregue na loja para continuar.'
                ),
            },
            status=409,
        )

    try:

        data = json.loads(
            request.body or '{}'
        )

        respostas = data.get(
            'respostas',
            [],
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'JSON inválido.',
            },
            status=400,
        )

    if not isinstance(
        respostas,
        list,
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Formato de respostas inválido.'
                ),
            },
            status=400,
        )

    questoes = list(
        fase.questoes
        .prefetch_related(
            'opcoes'
        )
        .order_by(
            'id'
        )
    )

    if not questoes:

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Esta fase ainda '
                    'não possui questões.'
                ),
            },
            status=400,
        )

    respostas_por_questao = {}

    for resposta in respostas:

        try:

            questao_id = int(
                resposta[
                    'questao_id'
                ]
            )

            opcao_id = int(
                resposta[
                    'opcao_id'
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            return JsonResponse(
                {
                    'status': 'erro',
                    'msg': (
                        'Uma das respostas '
                        'é inválida.'
                    ),
                },
                status=400,
            )

        if (
            questao_id
            in respostas_por_questao
        ):

            return JsonResponse(
                {
                    'status': 'erro',
                    'msg': (
                        'Uma questão recebeu '
                        'mais de uma resposta.'
                    ),
                },
                status=400,
            )

        respostas_por_questao[
            questao_id
        ] = opcao_id

    ids_questoes = {
        questao.id
        for questao in questoes
    }

    if (
        set(
            respostas_por_questao.keys()
        )
        != ids_questoes
    ):

        return JsonResponse(
            {
                'status': 'erro',
                'msg': (
                    'Responda todas as '
                    'questões antes de finalizar.'
                ),
            },
            status=400,
        )

    acertos = 0

    respostas_validadas = []

    for questao in questoes:

        opcao_id = (
            respostas_por_questao[
                questao.id
            ]
        )

        opcao = next(
            (
                opcao
                for opcao
                in questao.opcoes.all()
                if opcao.id
                == opcao_id
            ),
            None,
        )

        if opcao is None:

            return JsonResponse(
                {
                    'status': 'erro',
                    'msg': (
                        'Uma opção não '
                        'pertence à questão.'
                    ),
                },
                status=400,
            )

        correta = bool(
            opcao.e_correta
        )

        if correta:

            acertos += 1

        respostas_validadas.append(
            {
                'questao': questao,
                'opcao': opcao,
                'correta': correta,
            }
        )

    total = len(
        questoes
    )

    erros = (
        total
        - acertos
    )

    aproveitamento_decimal = (
        Decimal(acertos)
        / Decimal(total)
    )

    aproveitamento_percentual = (
        aproveitamento_decimal
        * Decimal('100')
    ).quantize(
        Decimal('0.01')
    )

    aprovado = (
        aproveitamento_decimal
        >= Decimal(
            str(
                APROVEITAMENTO_MINIMO
            )
        )
    )

    perfil = obter_perfil(
        request.user
    )

    modulo_concluido = False
    proximo_modulo_desbloqueado = False
    proximo_modulo_id = None
    proximo_modulo_titulo = None

    # --------------------------------------------------------
    # PROFESSOR
    #
    # Inclusive quando estiver usando o modo de teste.
    #
    # Não recebe progresso nem recompensa.
    # --------------------------------------------------------

    if usuario_e_professor(
        request
    ):

        return JsonResponse(
            {
                'status': 'ok',
                'aprovado': bool(
                    aprovado
                ),
                'concluida': bool(
                    aprovado
                ),
                'acertos': acertos,
                'erros': erros,
                'total': total,
                'aproveitamento': float(
                    aproveitamento_percentual
                ),
                'recompensa_xp': 0,
                'recompensa_moedas': 0,
                'concluida_pela_primeira_vez': (
                    False
                ),
                'proximo_minimo': int(
                    APROVEITAMENTO_MINIMO
                    * 100
                ),
                'modulo_concluido': False,
                'proximo_modulo_desbloqueado': False,
                'proximo_modulo_id': None,
                'proximo_modulo_titulo': None,
            }
        )

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    with transaction.atomic():

        perfil = (
            PerfilUsuario.objects
            .select_for_update()
            .get(
                pk=perfil.pk
            )
        )

        progresso, _ = (
            ProgressoFase.objects
            .get_or_create(
                perfil=perfil,
                fase=fase,
            )
        )

        fase_ja_concluida = (
            progresso.concluida
        )

        agora = timezone.now()

        progresso.tentativas += 1

        progresso.erros = erros

        progresso.data_ultima_tentativa = (
            agora
        )

        progresso.melhor_aproveitamento = (
            max(
                progresso.melhor_aproveitamento,
                aproveitamento_percentual,
            )
        )

        melhor_aproveitamento = (
            progresso.melhor_aproveitamento
        )

        recompensa_xp = 0

        recompensa_moedas = 0

        concluida_pela_primeira_vez = (
            False
        )

        if (
            aprovado
            and not progresso.concluida
        ):

            progresso.concluida = True

            progresso.data_conclusao = (
                agora
            )

            recompensa_xp = (
                fase.xp_recompensa
            )

            recompensa_moedas = (
                fase.moedas_recompensa
            )

            perfil.xp_total += (
                recompensa_xp
            )

            perfil.moedas += (
                recompensa_moedas
            )

            concluida_pela_primeira_vez = (
                True
            )

        progresso.save()

        if concluida_pela_primeira_vez:
            proximo_modulo = desbloquear_proximo_modulo(
                perfil,
                fase.modulo,
                agora,
            )

            modulo_concluido = modulo_esta_completo_para_aluno(
                perfil,
                fase.modulo,
            )

            if proximo_modulo is not None:
                proximo_modulo_desbloqueado = True
                proximo_modulo_id = proximo_modulo.id
                proximo_modulo_titulo = proximo_modulo.titulo

        campos_perfil_atualizados = []

        if (
            not aprovado
            and not fase_ja_concluida
        ):
            perfil.vidas = max(
                0,
                perfil.vidas - 1,
            )
            campos_perfil_atualizados.append(
                'vidas'
            )

        if (
            recompensa_xp
            or recompensa_moedas
        ):
            campos_perfil_atualizados.extend([
                'xp_total',
                'moedas',
            ])

        if campos_perfil_atualizados:
            perfil.save(
                update_fields=list(
                    dict.fromkeys(
                        campos_perfil_atualizados
                    )
                )
            )

        # ----------------------------------------------------
        # HISTÓRICO DA TENTATIVA
        # ----------------------------------------------------

        tentativa = (
            TentativaFase.objects.create(
                perfil=perfil,
                fase=fase,
                fase_titulo_snapshot=(
                    fase.titulo
                ),
                finalizada_em=agora,
                total_questoes=total,
                acertos=acertos,
                erros=erros,
                aproveitamento=(
                    aproveitamento_percentual
                ),
                aprovado=bool(
                    aprovado
                ),
                xp_ganho=recompensa_xp,
                moedas_ganhas=(
                    recompensa_moedas
                ),
            )
        )

        # ----------------------------------------------------
        # HISTÓRICO DAS RESPOSTAS
        # ----------------------------------------------------

        respostas_historicas = []

        for resposta in (
            respostas_validadas
        ):

            questao = (
                resposta['questao']
            )

            opcao = (
                resposta['opcao']
            )

            respostas_historicas.append(
                RespostaTentativa(
                    tentativa=tentativa,
                    questao=questao,
                    opcao_escolhida=opcao,
                    texto_questao_snapshot=(
                        questao.enunciado
                    ),
                    texto_opcao_snapshot=(
                        opcao.texto
                    ),
                    correta=(
                        resposta['correta']
                    ),
                )
            )

        RespostaTentativa.objects.bulk_create(
            respostas_historicas
        )

        tentativas_totais = (
            progresso.tentativas
        )

    concluida_na_plataforma = (
        fase_ja_concluida
        or bool(
            aprovado
        )
    )

    return JsonResponse(
        {
            'status': 'ok',
            'aprovado': bool(
                aprovado
            ),
            'concluida': (
                concluida_na_plataforma
            ),
            'acertos': acertos,
            'erros': erros,
            'total': total,
            'aproveitamento': float(
                aproveitamento_percentual
            ),
            'recompensa_xp': (
                recompensa_xp
            ),
            'recompensa_moedas': (
                recompensa_moedas
            ),
            'concluida_pela_primeira_vez': (
                concluida_pela_primeira_vez
            ),
            'tentativas_totais': (
                tentativas_totais
            ),
            'melhor_aproveitamento': (
                float(
                    melhor_aproveitamento
                )
            ),
            'modulo_concluido': modulo_concluido,
            'proximo_modulo_desbloqueado': proximo_modulo_desbloqueado,
            'proximo_modulo_id': proximo_modulo_id,
            'proximo_modulo_titulo': proximo_modulo_titulo,
            'tentativa_id': (
                tentativa.id
            ),
            'proximo_minimo': int(
                APROVEITAMENTO_MINIMO
                * 100
            ),
            'vidas': perfil.vidas,
            'perfil': {
                'xp_total': (
                    perfil.xp_total
                ),
                'moedas': (
                    perfil.moedas
                ),
                'vidas': perfil.vidas,
                'nivel': (
                    perfil.nivel
                ),
            },
        }
    )


# ============================================================
# 16. REVISÃO PEDAGÓGICA
# ============================================================

@login_required
def revisao_fase(request, fase_id):

    fase = get_object_or_404(
        Fase.objects.select_related(
            'modulo__disciplina'
        ),
        id=fase_id,
    )

    if usuario_e_professor(request):
        return redirect(
            'editar_trilha',
            trilha_id=fase.modulo.disciplina_id,
        )

    perfil = obter_perfil(request.user)

    ultima_tentativa = (
        TentativaFase.objects
        .filter(
            perfil=perfil,
            fase=fase,
            aprovado=False,
        )
        .prefetch_related(
            'respostas__questao__opcoes',
        )
        .order_by('-iniciada_em')
        .first()
    )

    respostas_revisao = []

    if ultima_tentativa:
        for resposta in ultima_tentativa.respostas.all():
            if resposta.correta:
                continue

            resposta.opcao_correta_atual = (
                resposta.questao.opcoes
                .filter(e_correta=True)
                .first()
                if resposta.questao
                else None
            )

            respostas_revisao.append(resposta)

    return render(
        request,
        'gamificacao/revisao_fase.html',
        {
            'fase': fase,
            'trilha_id': fase.modulo.disciplina_id,
            'perfil': perfil,
            'ultima_tentativa': ultima_tentativa,
            'respostas_revisao': respostas_revisao,
            'tema_aplicado': perfil.tema_fundo,
        },
    )


# ============================================================
# 16. HISTÓRICO
# ============================================================

@login_required
def historico_fase(
    request,
    fase_id,
):

    fase = get_object_or_404(
        Fase.objects.select_related(
            'modulo__disciplina'
        ),
        id=fase_id,
    )

    # --------------------------------------------------------
    # Professor, inclusive modo de teste
    # --------------------------------------------------------

    if usuario_e_professor(
        request
    ):

        return redirect(
            'editar_trilha',
            trilha_id=(
                fase.modulo.disciplina_id
            ),
        )

    perfil = obter_perfil(
        request.user
    )

    tentativas = list(
        (
            TentativaFase.objects
            .filter(
                perfil=perfil,
                fase=fase,
            )
            .prefetch_related(
                'respostas__questao',
                'respostas__opcao_escolhida',
            )
            .order_by(
                '-iniciada_em'
            )
        )
    )

    progresso = (
        ProgressoFase.objects
        .filter(
            perfil=perfil,
            fase=fase,
        )
        .first()
    )

    return render(
        request,
        'curriculo/historico_fase.html',
        {
            'fase': fase,
            'trilha_id': (
                fase.modulo.disciplina_id
            ),
            'tentativas': tentativas,
            'progresso': progresso,
            'perfil': perfil,
            'tema_aplicado': perfil.tema_fundo,
        },
    )