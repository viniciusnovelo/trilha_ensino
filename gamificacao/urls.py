from django.urls import path

from . import views


urlpatterns = [
    path(
        'tema/',
        views.atualizar_tema_usuario,
        name='atualizar_tema_usuario',
    ),

    path(
        'aparencia/',
        views.atualizar_aparencia_usuario,
        name='atualizar_aparencia_usuario',
    ),
    path(
        'loja/',
        views.loja,
        name='loja',
    ),
    path(
        'loja/comprar/<int:item_id>/',
        views.comprar_item,
        name='comprar_item',
    ),
    path(
        'perfil/',
        views.perfil_gamificacao,
        name='perfil_gamificacao',
    ),
]
