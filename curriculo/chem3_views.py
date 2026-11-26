"""Player e endpoints do jogo Química 3."""
import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import Fase, Questao, Opcao
from .rewards import conceder_moedas_por_questao
from .views import fase_esta_liberada, contexto_papel, papel_efetivo
from .chem3_engine import calculate, is_correct
from gamificacao.models import PerfilUsuario, TentativaFase, RespostaTentativa, ProgressoFase


def _safe_exercise(question, completed_ids):
    data = json.loads(json.dumps(question.dados_dinamicos or {}))
    answer = data.get('challenge', {}).get('answer', {})
    for key in ('correct', 'formula', 'tolerance', 'solution', 'explanation'):
        answer.pop(key, None)
    data.update({
        'phase_id': question.fase_id,
        'question_id': question.pk,
        'completed': question.fase_id in completed_ids,
        'db_choices': [
            {'id': option.pk, 'text': option.texto}
            for option in question.opcoes.all()
        ] if answer.get('type') == 'choice' else [],
    })
    return data


@login_required
@ensure_csrf_cookie
def chem3_player(request, fase_id):
    fase = get_object_or_404(
        Fase.objects.select_related('modulo__disciplina'),
        pk=fase_id, modulo__disciplina__slug='quimica-3',
    )
    if not fase_esta_liberada(request, fase):
        return HttpResponseForbidden('Esta fase ainda não está liberada.')

    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    all_phases = list(
        Fase.objects.filter(modulo__disciplina=fase.modulo.disciplina)
        .select_related('modulo')
        .prefetch_related('questoes__opcoes')
        .order_by('modulo__ordem', 'ordem', 'id')
    )
    completed_ids = set(
        ProgressoFase.objects.filter(
            perfil=perfil, concluida=True,
            fase__modulo__disciplina=fase.modulo.disciplina,
        ).values_list('fase_id', flat=True)
    )
    phase_rows, exercise_rows = [], []
    for module_index, module in enumerate(fase.modulo.disciplina.modulos.order_by('ordem'), start=1):
        module_phases = [item for item in all_phases if item.modulo_id == module.pk]
        ids = []
        for item in module_phases:
            question = item.questoes.all().first()
            if not question or not question.dados_dinamicos:
                continue
            source = _safe_exercise(question, completed_ids)
            source.update({
                'phase': module_index,
                'exercise_number': item.ordem,
                'completed': item.pk in completed_ids,
                'completion': source.get('completion', {'xp': item.xp_recompensa}),
            })
            exercise_rows.append(source)
            ids.append(source['id'])
        phase_rows.append({
            'number': module_index, 'title': module.titulo,
            'exercise_ids': ids, 'exercise_count': len(ids),
        })

    active_question = fase.questoes.first()
    if not active_question:
        return HttpResponseForbidden('Esta fase ainda não possui exercício.')
    payload = {
        'phases': phase_rows,
        'exercises': exercise_rows,
        'active_id': active_question.codigo_fonte,
        'active_phase_id': fase.pk,
        'xp_total': perfil.xp_total,
        'completed_ids': [item['id'] for item in exercise_rows if item['completed']],
        'urls': {
            'check': reverse('chem3_check_answer', args=[fase.pk]),
            'finish': reverse('chem3_finish_phase', args=[fase.pk]),
            'map': reverse('trilha', args=[fase.modulo.disciplina_id]),
        },
    }
    context = contexto_papel(request)
    context.update({
        'fase': fase, 'perfil': perfil,
        'tema_aplicado': perfil.tema_fundo if papel_efetivo(request) == 'aluno' else fase.modulo.disciplina.tema,
        'aparencia_interface': perfil.aparencia_interface,
        'chem3_payload': payload,
    })
    return render(request, 'curriculo/chem3_player.html', context)


@login_required
@require_POST
def chem3_check_answer(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id, modulo__disciplina__slug='quimica-3')
    if not fase_esta_liberada(request, fase):
        return JsonResponse({'error': 'Esta fase ainda não está liberada.'}, status=403)
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    try:
        payload = json.loads(request.body or '{}')
        question = get_object_or_404(Questao, pk=int(payload['questao_id']), fase=fase)
        answer = question.dados_dinamicos['challenge']['answer']
        specs = question.dados_dinamicos.get('simulation', {}).get('parameters', [])
        allowed = {spec['key']: spec for spec in specs}
        supplied = payload.get('parameters') or {}
        if set(supplied) - set(allowed):
            return JsonResponse({'error': 'Parâmetro desconhecido.'}, status=400)
        params = {key: float(supplied.get(key, spec['value'])) for key, spec in allowed.items()}
        for key, value in params.items():
            spec = allowed[key]
            if not spec['min'] <= value <= spec['max']:
                return JsonResponse({'error': f'Parâmetro fora do limite: {key}.'}, status=400)
            steps = (value - float(spec['min'])) / float(spec['step'])
            if abs(steps - round(steps)) > 1e-6:
                return JsonResponse({'error': f'Incremento inválido: {key}.'}, status=400)

        kind = answer['type']
        chosen = None
        expected = None
        if kind == 'choice':
            chosen = get_object_or_404(Opcao, pk=int(payload['option_id']), questao=question)
            correct = chosen.e_correta
            submitted = {'option_id': chosen.pk, 'text': chosen.texto}
            right = question.opcoes.filter(e_correta=True).first()
            snapshot = {'option_id': right.pk, 'text': right.texto} if right else {}
        elif kind in ('dynamic_choice', 'numeric', 'pair_numeric'):
            expected = calculate(answer['formula'], params)
            if kind == 'dynamic_choice':
                submitted_value = str(payload.get('value', ''))
                valid = {str(item.get('value')) for item in answer.get('choices', []) if isinstance(item, dict)}
                if submitted_value not in valid:
                    return JsonResponse({'error': 'Alternativa inválida.'}, status=400)
                correct = is_correct(submitted_value, expected)
                submitted = {'value': submitted_value}
                snapshot = {'value': expected}
            elif kind == 'pair_numeric':
                values = payload.get('values')
                if not isinstance(values, list) or len(values) != len(answer.get('components', [])):
                    return JsonResponse({'error': 'Informe todos os valores solicitados.'}, status=400)
                correct = is_correct(values, expected, answer.get('tolerance', 0))
                submitted = {'values': values, 'components': answer['components']}
                snapshot = {'values': expected, 'components': answer['components']}
            else:
                value = payload.get('value')
                if value is None:
                    return JsonResponse({'error': 'Informe um valor.'}, status=400)
                correct = is_correct(value, expected, answer.get('tolerance', 0))
                submitted = {'value': value, 'unit': answer.get('display_unit', '')}
                snapshot = {'value': expected, 'unit': answer.get('display_unit', '')}
        else:
            return JsonResponse({'error': 'Tipo de resposta não suportado.'}, status=400)

        feedback = answer.get('explanation', 'Resposta correta.') if correct else answer.get('hint', 'Revise a simulação e tente novamente.')
        attempt, _ = TentativaFase.objects.get_or_create(
            perfil=perfil, fase=fase, finalizada_em__isnull=True,
            defaults={'fase_titulo_snapshot': fase.titulo, 'total_questoes': 1},
        )
        with transaction.atomic():
            RespostaTentativa.objects.update_or_create(
                tentativa=attempt, questao=question,
                defaults={
                    'opcao_escolhida': chosen,
                    'texto_questao_snapshot': question.enunciado,
                    'texto_opcao_snapshot': chosen.texto if chosen else '',
                    'correta': correct,
                    'tipo_resposta_snapshot': 'choice' if kind in {'choice', 'dynamic_choice'} else 'numeric',
                    'resposta_snapshot': submitted,
                    'resposta_correta_snapshot': snapshot,
                    'parametros_snapshot': params,
                    'feedback_snapshot': feedback,
                },
            )
        request.session[f'chem3_attempt_{fase.pk}'] = attempt.pk
        return JsonResponse({
            'correct': correct, 'feedback': feedback,
            'hint': '' if correct else answer.get('hint', ''),
            'unit': answer.get('display_unit', ''),
        })
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        return JsonResponse({'error': f'Resposta inválida: {exc}'}, status=400)


@login_required
@require_POST
@transaction.atomic
def chem3_finish_phase(request, fase_id):
    fase = get_object_or_404(Fase, pk=fase_id, modulo__disciplina__slug='quimica-3')
    attempt_id = request.session.get(f'chem3_attempt_{fase.pk}')
    if not attempt_id:
        return JsonResponse({'error': 'Tentativa não encontrada.'}, status=409)
    attempt = get_object_or_404(
        TentativaFase.objects.select_for_update(),
        pk=attempt_id, perfil__usuario=request.user, fase=fase,
    )
    if attempt.finalizada_em:
        return JsonResponse({'status': 'ok', 'aprovado': attempt.aprovado, 'moedas_ganhas': attempt.moedas_ganhas, 'xp_ganho': attempt.xp_ganho})
    answers = list(attempt.respostas.select_related('questao').all())
    correct = sum(item.correta for item in answers)
    approved = len(answers) == 1 and correct == 1
    percent = Decimal(100 if approved else 0)
    xp = int(answers[0].questao.dados_dinamicos.get('completion', {}).get('xp', fase.xp_recompensa)) if approved and answers else 0
    attempt.acertos = correct
    attempt.erros = max(0, len(answers) - correct)
    attempt.aproveitamento = percent
    attempt.aprovado = approved
    attempt.xp_ganho = xp
    attempt.finalizada_em = timezone.now()
    attempt.save(update_fields=['acertos', 'erros', 'aproveitamento', 'aprovado', 'xp_ganho', 'finalizada_em'])
    coins = conceder_moedas_por_questao(attempt, answers) if approved else 0
    if approved:
        attempt.perfil.xp_total += xp
        attempt.perfil.save(update_fields=['xp_total'])
    progress, _ = ProgressoFase.objects.get_or_create(perfil=attempt.perfil, fase=fase)
    progress.tentativas += 1
    progress.erros += attempt.erros
    progress.data_ultima_tentativa = timezone.now()
    progress.melhor_aproveitamento = max(progress.melhor_aproveitamento, percent)
    if approved:
        progress.concluida = True
        progress.data_conclusao = timezone.now()
    progress.save()
    request.session.pop(f'chem3_attempt_{fase.pk}', None)
    return JsonResponse({
        'status': 'ok', 'aprovado': approved, 'acertos': correct,
        'erros': attempt.erros, 'total': 1,
        'aproveitamento': float(percent), 'xp_ganho': xp,
        'moedas_ganhas': coins,
    })
