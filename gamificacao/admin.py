from django.contrib import admin

from .models import (
    PerfilUsuario,
    ItemLoja,
    ItemComprado,
    ProgressoFase,
    TentativaFase,
    RespostaTentativa,
)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'tipo',
        'xp_total',
        'nivel',
        'moedas',
        'vidas',
        'tema_fundo',
        'aparencia_interface',
    )

    list_filter = (
        'tipo',
        'tema_fundo',
        'aparencia_interface',
    )

    search_fields = (
        'usuario__username',
        'usuario__email',
    )


@admin.register(ItemLoja)
class ItemLojaAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'tipo',
        'preco_moedas',
    )

    list_filter = (
        'tipo',
    )

    search_fields = (
        'nome',
        'descricao',
    )


@admin.register(ItemComprado)
class ItemCompradoAdmin(admin.ModelAdmin):

    list_display = (
        'perfil',
        'item',
        'equipado',
        'data_aquisicao',
    )

    list_filter = (
        'equipado',
        'item__tipo',
    )

    search_fields = (
        'perfil__usuario__username',
        'item__nome',
    )


@admin.register(ProgressoFase)
class ProgressoFaseAdmin(admin.ModelAdmin):

    list_display = (
        'perfil',
        'fase',
        'concluida',
        'tentativas',
        'melhor_aproveitamento',
        'data_ultima_tentativa',
        'data_conclusao',
    )

    list_filter = (
        'concluida',
        'fase__modulo__disciplina',
    )

    search_fields = (
        'perfil__usuario__username',
        'fase__titulo',
    )


class RespostaTentativaInline(admin.TabularInline):
    model = RespostaTentativa

    extra = 0

    readonly_fields = (
        'questao',
        'opcao_escolhida',
        'texto_questao_snapshot',
        'texto_opcao_snapshot',
        'correta',
        'respondida_em',
    )

    can_delete = False


@admin.register(TentativaFase)
class TentativaFaseAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'perfil',
        'fase_titulo_snapshot',
        'aproveitamento',
        'acertos',
        'erros',
        'aprovado',
        'xp_ganho',
        'moedas_ganhas',
        'iniciada_em',
    )

    list_filter = (
        'aprovado',
        'fase__modulo__disciplina',
    )

    search_fields = (
        'perfil__usuario__username',
        'fase_titulo_snapshot',
    )

    readonly_fields = (
        'perfil',
        'fase',
        'fase_titulo_snapshot',
        'iniciada_em',
        'finalizada_em',
        'total_questoes',
        'acertos',
        'erros',
        'aproveitamento',
        'aprovado',
        'xp_ganho',
        'moedas_ganhas',
    )

    inlines = [
        RespostaTentativaInline,
    ]


@admin.register(RespostaTentativa)
class RespostaTentativaAdmin(admin.ModelAdmin):

    list_display = (
        'tentativa',
        'questao',
        'opcao_escolhida',
        'correta',
        'respondida_em',
    )

    list_filter = (
        'correta',
    )

    search_fields = (
        'texto_questao_snapshot',
        'texto_opcao_snapshot',
        'tentativa__perfil__usuario__username',
    )

    readonly_fields = (
        'tentativa',
        'questao',
        'opcao_escolhida',
        'texto_questao_snapshot',
        'texto_opcao_snapshot',
        'correta',
        'respondida_em',
    )