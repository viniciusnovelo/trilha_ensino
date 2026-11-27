"""Registro atômico de respostas e consumo de vidas dos alunos."""
from django.db import transaction
from .models import PerfilUsuario, TentativaFase, RespostaTentativa


@transaction.atomic
def registrar_resposta_com_vida(attempt, question, defaults, consumir_vida=True):
    """Registra uma resposta uma única vez por questão/tentativa.

    Requisições repetidas retornam o registro existente e nunca descontam
    uma segunda vida. O saldo é atualizado no servidor sob bloqueio de linha.
    """
    tentativa = TentativaFase.objects.select_for_update().get(pk=attempt.pk)
    perfil = PerfilUsuario.objects.select_for_update().get(pk=tentativa.perfil_id)
    resposta = RespostaTentativa.objects.filter(
        tentativa=tentativa, questao=question
    ).first()
    if resposta:
        return resposta, perfil.vidas, False, False

    if consumir_vida and perfil.vidas <= 0:
        return None, perfil.vidas, False, True

    resposta = RespostaTentativa.objects.create(
        tentativa=tentativa, questao=question, **defaults
    )
    if consumir_vida and not resposta.correta:
        perfil.vidas -= 1
        perfil.save(update_fields=["vidas"])
    return resposta, perfil.vidas, True, False
