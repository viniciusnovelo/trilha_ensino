import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import ItemLoja, PerfilUsuario


DEFAULT_ITENS_LOJA = [
    {
        'nome': 'Recarga completa de vidas',
        'descricao': 'Restaura suas vidas até o máximo de 5.',
        'preco_moedas': 30,
    },
    {
        'nome': 'Recarga econômica de vidas',
        'descricao': 'Adiciona até 2 vidas, respeitando o máximo de 5.',
        'preco_moedas': 18,
    },
]


def obter_perfil(usuario):
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=usuario
    )
    return perfil


def modo_professor_teste(request):
    return bool(
        getattr(settings, 'DEBUG', False)
        and request.user.is_authenticated
        and (
            request.user.is_staff
            or request.user.is_superuser
        )
        and request.session.get('modo_teste')
        == 'professor'
    )


@login_required
@require_POST
def atualizar_tema_usuario(request):
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

    tema = data.get('tema')

    temas_validos = {
        valor
        for valor, _
        in PerfilUsuario.TEMAS
    }

    if tema not in temas_validos:
        return JsonResponse(
            {
                'status': 'erro',
                'msg': 'Tema inválido.',
            },
            status=400,
        )

    perfil = obter_perfil(
        request.user
    )

    perfil.tema_fundo = tema

    perfil.save(
        update_fields=[
            'tema_fundo'
        ]
    )

    return JsonResponse(
        {
            'status': 'ok',
            'tema': tema,
            'tema_display': (
                perfil.get_tema_fundo_display()
            ),
        }
    )


def garantir_itens_padrao():
    for item in DEFAULT_ITENS_LOJA:
        ItemLoja.objects.get_or_create(
            nome=item['nome'],
            defaults={
                'descricao': item['descricao'],
                'preco_moedas': item['preco_moedas'],
                'tipo': 'vida',
            },
        )


@login_required
def loja(request):

    if modo_professor_teste(request):
        return redirect(
            'dashboard_professor'
        )

    perfil = obter_perfil(
        request.user
    )

    garantir_itens_padrao()

    itens = (
        ItemLoja.objects
        .filter(
            tipo='vida'
        )
        .order_by(
            'preco_moedas',
            'id',
        )
    )

    return render(
        request,
        'gamificacao/loja.html',
        {
            'perfil': perfil,
            'itens': itens,
            'tema_aplicado': perfil.tema_fundo,
        },
    )


@login_required
@require_POST
def comprar_item(request, item_id):

    if modo_professor_teste(request):
        return redirect(
            'dashboard_professor'
        )

    item = get_object_or_404(
        ItemLoja,
        id=item_id,
        tipo='vida',
    )

    with transaction.atomic():

        perfil = (
            PerfilUsuario.objects
            .select_for_update()
            .get(
                usuario=request.user
            )
        )

        if perfil.vidas >= perfil.VIDAS_MAXIMAS:
            messages.info(
                request,
                'Você já está com o máximo de vidas.',
            )
            return redirect('loja')

        if perfil.moedas < item.preco_moedas:
            messages.error(
                request,
                'Você não possui moedas suficientes.',
            )
            return redirect('loja')

        perfil.moedas -= item.preco_moedas

        if 'completa' in item.nome.lower():
            perfil.vidas = perfil.VIDAS_MAXIMAS
        else:
            perfil.vidas = min(
                perfil.VIDAS_MAXIMAS,
                perfil.vidas + 2,
            )

        perfil.save(
            update_fields=[
                'moedas',
                'vidas',
            ]
        )

    messages.success(
        request,
        'Recarga realizada com sucesso.',
    )

    return redirect('loja')


@login_required
def perfil_gamificacao(request):

    if modo_professor_teste(request):
        return redirect(
            'dashboard_professor'
        )

    perfil = obter_perfil(
        request.user
    )

    return render(
        request,
        'gamificacao/perfil.html',
        {
            'perfil': perfil,
            'tema_aplicado': perfil.tema_fundo,
        },
    )
