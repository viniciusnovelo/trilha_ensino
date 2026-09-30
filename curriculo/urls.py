from django.urls import path

from . import views


urlpatterns = [

    path(
        'contas/cadastro/',
        views.cadastro_usuario,
        name='cadastro_usuario',
    ),


    # ========================================================
    # ROTEAMENTO
    # ========================================================

    path(
        '',
        views.redirecionamento_inicial,
        name='redirecionamento_inicial',
    ),

    path(
        'alternar-papel/',
        views.alternar_papel,
        name='alternar_papel',
    ),

    # ========================================================
    # DASHBOARDS
    # ========================================================

    path(
        'jogar/',
        views.dashboard_aluno,
        name='dashboard_aluno',
    ),

    path(
        'estudio/',
        views.dashboard_professor,
        name='dashboard_professor',
    ),

    # ========================================================
    # TRILHAS
    # ========================================================

    path(
        'estudio/nova-trilha/',
        views.criar_trilha,
        name='criar_trilha',
    ),

    path(
        'estudio/trilha/<int:trilha_id>/',
        views.editar_trilha,
        name='editar_trilha',
    ),

    path(
        'estudio/trilha/<int:trilha_id>/excluir/',
        views.deletar_trilha,
        name='deletar_trilha',
    ),

    path(
        'estudio/trilha/<int:trilha_id>/publicar/',
        views.alternar_publicacao,
        name='alternar_publicacao',
    ),

    # ========================================================
    # EDITOR VISUAL
    # ========================================================

    path(
        'estudio/trilha/<int:trilha_id>/atualizar-tema/',
        views.ajax_atualizar_tema,
        name='ajax_atualizar_tema',
    ),

    path(
        'estudio/fase/<int:fase_id>/atualizar-y/',
        views.atualizar_y_fase,
        name='atualizar_y_fase',
    ),

    # ========================================================
    # MODAIS AJAX
    # ========================================================

    path(
        'estudio/trilha/<int:trilha_id>/ajax/modulo/',
        views.ajax_criar_modulo,
        name='ajax_criar_modulo',
    ),

    path(
        'estudio/trilha/<int:trilha_id>/ajax/fase/',
        views.ajax_criar_fase,
        name='ajax_criar_fase',
    ),

    path(
        'estudio/ajax/questao/',
        views.ajax_criar_questao,
        name='ajax_criar_questao',
    ),

    path(
        'estudio/ajax/modulo/<int:modulo_id>/editar/',
        views.ajax_editar_modulo,
        name='ajax_editar_modulo',
    ),

    path(
        'estudio/ajax/modulo/<int:modulo_id>/excluir/',
        views.ajax_excluir_modulo,
        name='ajax_excluir_modulo',
    ),

    path(
        'estudio/ajax/fase/<int:fase_id>/editar/',
        views.ajax_editar_fase,
        name='ajax_editar_fase',
    ),

    path(
        'estudio/ajax/fase/<int:fase_id>/excluir/',
        views.ajax_excluir_fase,
        name='ajax_excluir_fase',
    ),

    path(
        'estudio/ajax/questao/<int:questao_id>/editar/',
        views.ajax_editar_questao,
        name='ajax_editar_questao',
    ),

    path(
        'estudio/ajax/questao/<int:questao_id>/excluir/',
        views.ajax_excluir_questao,
        name='ajax_excluir_questao',
    ),

    # ========================================================
    # JOGO
    # ========================================================

    path(
        'modulo/<int:modulo_id>/desbloquear/',
        views.desbloquear_modulo,
        name='desbloquear_modulo',
    ),

    path(
        'trilha/<int:trilha_id>/',
        views.trilha_view,
        name='trilha',
    ),

    path(
        'fase/<int:fase_id>/',
        views.fase_detalhe,
        name='fase_detalhe',
    ),

    path(
        'fase/<int:fase_id>/verificar-resposta/',
        views.verificar_resposta,
        name='verificar_resposta',
    ),

    path(
        'fase/<int:fase_id>/finalizar/',
        views.finalizar_fase,
        name='finalizar_fase',
    ),

    # ========================================================
    # HISTÓRICO
    # ========================================================

    path(
        'fase/<int:fase_id>/revisao/',
        views.revisao_fase,
        name='revisao_fase',
    ),

    path(
        'fase/<int:fase_id>/historico/',
        views.historico_fase,
        name='historico_fase',
    ),
]