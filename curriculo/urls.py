from django.urls import path

from . import views
from . import physics_views
from . import math1_views
from . import math2_views
from . import math3_views
from . import chem1_views
from . import chem2_views
from . import chem3_views


urlpatterns = [
    path('quimica3/fase/<int:fase_id>/', chem3_views.chem3_player, name='chem3_player'),
    path('quimica3/fase/<int:fase_id>/verificar-resposta/', chem3_views.chem3_check_answer, name='chem3_check_answer'),
    path('quimica3/fase/<int:fase_id>/finalizar/', chem3_views.chem3_finish_phase, name='chem3_finish_phase'),
    path('quimica2/fase/<int:fase_id>/', chem2_views.chem2_player, name='chem2_player'),
    path('quimica2/fase/<int:fase_id>/verificar-resposta/', chem2_views.chem2_check_answer, name='chem2_check_answer'),
    path('quimica2/fase/<int:fase_id>/finalizar/', chem2_views.chem2_finish_phase, name='chem2_finish_phase'),
    path('quimica1/fase/<int:fase_id>/', chem1_views.chem1_player, name='chem1_player'),
    path('quimica1/fase/<int:fase_id>/verificar-resposta/', chem1_views.chem1_check_answer, name='chem1_check_answer'),
    path('quimica1/fase/<int:fase_id>/finalizar/', chem1_views.chem1_finish_phase, name='chem1_finish_phase'),
    path('matematica3/fase/<int:fase_id>/', math3_views.math3_player, name='math3_player'),
    path('matematica3/fase/<int:fase_id>/responder/', math3_views.math3_check_answer, name='math3_check_answer'),
    path('matematica3/fase/<int:fase_id>/finalizar/', math3_views.math3_finish_phase, name='math3_finish_phase'),
    path('matematica2/fase/<int:fase_id>/', math2_views.math2_player, name='math2_player'),
    path('matematica2/fase/<int:fase_id>/responder/', math2_views.math2_check_answer, name='math2_check_answer'),
    path('matematica2/fase/<int:fase_id>/finalizar/', math2_views.math2_finish_phase, name='math2_finish_phase'),
    path('matematica1/fase/<int:fase_id>/', math1_views.math1_player, name='math1_player'),
    path('matematica1/fase/<int:fase_id>/verificar-resposta/', math1_views.math1_check_answer, name='math1_check_answer'),
    path('matematica1/fase/<int:fase_id>/finalizar/', math1_views.math1_finish_phase, name='math1_finish_phase'),
    path('fisica/fase/<int:fase_id>/', physics_views.physics_player, name='physics_player'),
    path('fisica/fase/<int:fase_id>/verificar-resposta/', physics_views.physics_check_answer, name='physics_check_answer'),
    path('fisica/fase/<int:fase_id>/finalizar/', physics_views.physics_finish_phase, name='physics_finish_phase'),

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
        'jogar/materia/<slug:materia_slug>/',
        views.materia_detalhe,
        name='materia_detalhe',
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