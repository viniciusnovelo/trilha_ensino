"""Recompensas de moedas por questão, concedidas uma única vez por aluno."""
from django.db.models import F

from .models import Questao
from gamificacao.models import PerfilUsuario, RespostaTentativa


def conceder_moedas_por_questao(attempt, answers):
    """
    Concede a posição da questão dentro do módulo em moedas.
    Deve ser chamada dentro de transaction.atomic(), após finalizar a tentativa.
    O bloqueio do perfil serializa créditos concorrentes do mesmo aluno.
    """
    perfil = PerfilUsuario.objects.select_for_update().get(pk=attempt.perfil_id)
    question_ids = list(
        Questao.objects.filter(
            fase__modulo_id=attempt.fase.modulo_id,
        ).order_by(
            "fase__ordem", "fase_id", "id",
        ).values_list("id", flat=True)
    )
    positions = {question_id: index + 1 for index, question_id in enumerate(question_ids)}
    coins_earned = 0

    for answer in answers:
        question_id = answer.questao_id
        if not answer.correta or not question_id or question_id not in positions:
            continue

        already_rewarded = RespostaTentativa.objects.filter(
            tentativa__perfil_id=perfil.pk,
            tentativa__finalizada_em__isnull=False,
            questao_id=question_id,
            correta=True,
        ).exclude(tentativa_id=attempt.pk).exists()
        if already_rewarded:
            continue

        coins_earned += positions[question_id]

    if coins_earned:
        perfil.moedas = F("moedas") + coins_earned
        perfil.save(update_fields=["moedas"])
        perfil.refresh_from_db(fields=["moedas"])

    attempt.moedas_ganhas = coins_earned
    attempt.save(update_fields=["moedas_ganhas"])
    return coins_earned
