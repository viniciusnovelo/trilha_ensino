"""Endpoints do player dinâmico de Física (integrados aos models existentes)."""
from __future__ import annotations
import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Fase, Questao, Opcao
from .views import fase_esta_liberada, contexto_papel, papel_efetivo
from .physics_engine import calculate, is_correct
from gamificacao.models import PerfilUsuario, TentativaFase, RespostaTentativa, ProgressoFase


def _question_payload(question):
    data = question.dados_dinamicos
    challenge = data['challenge']
    simulation = data['simulation']
    return {
        'id': question.id,
        'source_id': question.codigo_fonte,
        'title': data['title'],
        'topic': data['topic'],
        'context': data['context'],
        'prompt': challenge['prompt'],
        'type': question.tipo_resposta,
        'hint': challenge.get('hint') or challenge.get('answer', {}).get('hint', ''),
        'simulation': simulation,
        'options': [{'id': option.id, 'text': option.texto} for option in question.opcoes.all()] if question.tipo_resposta == 'choice' else [],
    }


@login_required
@ensure_csrf_cookie
def physics_player(request, fase_id):
    fase = get_object_or_404(Fase.objects.select_related('modulo__disciplina'), pk=fase_id)
    if not fase_esta_liberada(request, fase):
        return HttpResponseForbidden('Esta fase ainda não está liberada.')
    questions = list(fase.questoes.prefetch_related('opcoes').order_by('id'))
    if not questions or any(not q.dados_dinamicos for q in questions):
        return HttpResponseBadRequest('Esta fase não contém conteúdo dinâmico de Física.')
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    attempt = TentativaFase.objects.create(
        perfil=perfil, fase=fase, fase_titulo_snapshot=fase.titulo,
        total_questoes=len(questions),
    )
    request.session['physics_attempt_id'] = attempt.pk
    request.session['physics_phase_id'] = fase.pk
    fases_modulo = list(fase.modulo.fases.order_by('ordem', 'id'))
    posicao_fase = next(
        (indice for indice, item in enumerate(fases_modulo, start=1) if item.id == fase.id),
        1,
    )
    payload = {
        'phase': {
            'id': fase.id,
            'title': fase.titulo,
            'module_title': fase.modulo.titulo,
            'order': posicao_fase,
            'total_phases': len(fases_modulo),
        },
        'attempt_id': attempt.pk,
        'questions': [_question_payload(q) for q in questions],
    }
    papel = papel_efetivo(request)
    tema_aplicado = (
        perfil.tema_fundo
        if papel == 'aluno'
        else fase.modulo.disciplina.tema
    )
    contexto = contexto_papel(request)
    contexto.update({
        'fase': fase,
        'player_payload': payload,
        'tema_fundo': perfil.tema_fundo,
        'tema_aplicado': tema_aplicado,
        'aparencia_interface': perfil.aparencia_interface,
    })
    return render(request, 'curriculo/physics_player.html', contexto)


@login_required
@require_POST
def physics_check_answer(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    attempt_id = request.session.get('physics_attempt_id')
    if not attempt_id or request.session.get('physics_phase_id') != fase.id:
        return JsonResponse({'error': 'Tentativa não encontrada. Reabra a fase.'}, status=409)
    attempt = get_object_or_404(TentativaFase, pk=attempt_id, perfil__usuario=request.user, fase=fase, finalizada_em__isnull=True)
    try:
        payload = json.loads(request.body or '{}')
        question = get_object_or_404(Questao, pk=int(payload['questao_id']), fase=fase)
        dynamic = question.dados_dinamicos
        answer = dynamic['challenge']['answer']
        source_parameters = dynamic['simulation']['parameters']
        allowed = {item['key']: item for item in source_parameters}
        supplied = payload.get('parameters') or {}
        if set(supplied) - set(allowed):
            return JsonResponse({'error': 'Parâmetros desconhecidos.'}, status=400)
        parameters = {key: float(supplied.get(key, item['value'])) for key, item in allowed.items()}
        for key, value in parameters.items():
            item = allowed[key]
            if not item['min'] <= value <= item['max']:
                return JsonResponse({'error': f'Parâmetro fora do limite: {key}.'}, status=400)
            steps = (value - float(item['min'])) / float(item['step'])
            if abs(steps - round(steps)) > 1e-6:
                return JsonResponse({'error': f'Parâmetro não respeita o incremento configurado: {key}.'}, status=400)
        from .physics_engine import validate_scene_parameters
        validate_scene_parameters(dynamic['simulation']['scene'], parameters)
        if question.tipo_resposta == 'choice':
            option = get_object_or_404(Opcao, pk=int(payload['opcao_id']), questao=question)
            correct = bool(option.e_correta)
            submitted_snapshot = {'option_id': option.pk, 'text': option.texto}
            correct_option = question.opcoes.filter(e_correta=True).first()
            correct_snapshot = {'option_id': correct_option.pk, 'text': correct_option.texto}
            feedback = answer.get('explanation', '')
            chosen_option = option
            expected_value = None
        else:
            submitted = float(payload['valor'])
            if dynamic.get('id') == 'fis1-ene-08' and parameters.get('hf', 0) >= parameters.get('hi', 0):
                return JsonResponse({'error': 'A altura final deve ser menor que a altura inicial.'}, status=400)
            constants = dynamic.get('source_constants', {})
            expected_value = calculate(answer['formula'], parameters, constants)
            correct = is_correct(submitted, expected_value, answer['tolerance'])
            submitted_snapshot = {'value': submitted, 'unit': answer.get('unit', '')}
            correct_snapshot = {'value': expected_value, 'unit': answer.get('unit', '')}
            feedback = ('Resposta correta.' if correct else answer.get('solution', answer.get('explanation', 'Revise a relação física e tente novamente.')))
            chosen_option = None
        with transaction.atomic():
            RespostaTentativa.objects.update_or_create(
                tentativa=attempt, questao=question,
                defaults={
                    'opcao_escolhida': chosen_option,
                    'texto_questao_snapshot': question.enunciado,
                    'texto_opcao_snapshot': chosen_option.texto if chosen_option else '',
                    'correta': correct,
                    'tipo_resposta_snapshot': question.tipo_resposta,
                    'resposta_snapshot': submitted_snapshot,
                    'resposta_correta_snapshot': correct_snapshot,
                    'parametros_snapshot': parameters,
                    'feedback_snapshot': feedback,
                },
            )
        return JsonResponse({'correct': correct, 'feedback': feedback,
                              'hint': '' if correct else (dynamic['challenge'].get('hint') or answer.get('hint', '')),
                              'expected_display': None if question.tipo_resposta == 'choice' else round(expected_value, answer.get('digits', 2)),
                              'unit': answer.get('display_unit', answer.get('unit', ''))})
    except (KeyError, TypeError, ValueError) as exc:
        return JsonResponse({'error': f'Resposta inválida: {exc}'}, status=400)


@login_required
@require_POST
def physics_finish_phase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id)
    attempt_id = request.session.get('physics_attempt_id')
    if not attempt_id or request.session.get('physics_phase_id') != fase.id:
        return JsonResponse({'error': 'Tentativa não encontrada.'}, status=409)
    attempt = get_object_or_404(TentativaFase, pk=attempt_id, perfil__usuario=request.user, fase=fase)
    if attempt.finalizada_em:
        return JsonResponse({'status': 'ok', 'aprovado': attempt.aprovado, 'aproveitamento': float(attempt.aproveitamento)})
    answers = list(attempt.respostas.all())
    total = attempt.total_questoes
    correct = sum(1 for item in answers if item.correta)
    percent = (Decimal(correct) * Decimal('100') / Decimal(total)) if total else Decimal('0')
    approved = percent >= Decimal('60') and len(answers) == total
    xp = 0
    if approved:
        for item in answers:
            if item.correta and item.questao_id:
                xp += int(item.questao.dados_dinamicos.get('completion', {}).get('xp', 0))
    attempt.acertos = correct
    attempt.erros = max(0, len(answers) - correct)
    attempt.aproveitamento = percent
    attempt.aprovado = approved
    attempt.xp_ganho = xp
    attempt.finalizada_em = timezone.now()
    attempt.save(update_fields=['acertos', 'erros', 'aproveitamento', 'aprovado', 'xp_ganho', 'finalizada_em'])
    progress, _ = ProgressoFase.objects.get_or_create(perfil=attempt.perfil, fase=fase)
    progress.tentativas += 1
    progress.erros += attempt.erros
    progress.data_ultima_tentativa = timezone.now()
    progress.melhor_aproveitamento = max(progress.melhor_aproveitamento, percent)
    if approved:
        perfil = attempt.perfil
        perfil.xp_total += xp
        perfil.save(update_fields=['xp_total'])
        progress.concluida = True
        progress.data_conclusao = timezone.now()
    progress.save()
    request.session.pop('physics_attempt_id', None)
    request.session.pop('physics_phase_id', None)
    return JsonResponse({'status': 'ok', 'aprovado': approved, 'acertos': correct,
                         'erros': attempt.erros, 'total': total,
                         'aproveitamento': float(percent), 'xp_ganho': xp})