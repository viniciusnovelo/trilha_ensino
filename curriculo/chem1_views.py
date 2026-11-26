"""Player e endpoints do jogo Química 1."""
import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse,HttpResponseForbidden,HttpResponseBadRequest
from django.shortcuts import get_object_or_404,render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Fase,Questao,Opcao
from .rewards import conceder_moedas_por_questao
from .views import fase_esta_liberada,contexto_papel,papel_efetivo
from .chem1_engine import calculate,is_correct
from gamificacao.models import PerfilUsuario,TentativaFase,RespostaTentativa,ProgressoFase

def _public_exercise(q):
    data=json.loads(json.dumps(q.dados_dinamicos or {}))
    answer=data.get('challenge',{}).get('answer',{})
    for key in ('correct','formula','tolerance','solution','explanation'): answer.pop(key,None)
    return data

@login_required
@ensure_csrf_cookie
def chem1_player(request, fase_id):
    fase = get_object_or_404(Fase.objects.select_related('modulo__disciplina'), pk=fase_id, modulo__disciplina__slug='quimica-1')
    if not fase_esta_liberada(request, fase):
        return HttpResponseForbidden('Esta fase ainda não está liberada.')
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    attempt = TentativaFase.objects.create(perfil=perfil, fase=fase, fase_titulo_snapshot=fase.titulo, total_questoes=1)
    request.session['chem1_attempt_id'] = attempt.pk
    request.session['chem1_phase_id'] = fase.pk

    all_phases = list(Fase.objects.filter(modulo__disciplina=fase.modulo.disciplina).select_related('modulo').prefetch_related('questoes__opcoes').order_by('modulo__ordem','ordem','id'))
    phase_rows = []
    exercise_rows = []
    completed_ids = set(ProgressoFase.objects.filter(perfil=perfil, concluida=True, fase__modulo__disciplina=fase.modulo.disciplina).values_list('fase_id', flat=True))
    for module_index, module in enumerate(fase.modulo.disciplina.modulos.order_by('ordem'), start=1):
        module_phases = [item for item in all_phases if item.modulo_id == module.pk]
        ids = []
        for item in module_phases:
            question = item.questoes.all().first()
            if not question or not question.dados_dinamicos:
                continue
            source = json.loads(json.dumps(question.dados_dinamicos))
            answer = source['challenge']['answer']
            answer.pop('correct', None)
            answer.pop('formula', None)
            answer.pop('tolerance', None)
            source.update({
                'phase': module_index,
                'phase_id': item.pk,
                'question_id': question.pk,
                'exercise_number': item.ordem,
                'completed': item.pk in completed_ids,
                'completion': source.get('completion', {'xp': item.xp_recompensa}),
            })
            if answer.get('type') == 'choice':
                source['db_choices'] = [{'id': option.pk, 'text': option.texto} for option in question.opcoes.all()]
            else:
                source['db_choices'] = []
            exercise_rows.append(source)
            ids.append(source['id'])
        phase_rows.append({'number': module_index, 'title': module.titulo, 'exercise_ids': ids, 'exercise_count': len(ids)})
    active_question = fase.questoes.first()
    active_id = active_question.codigo_fonte
    safe_payload = {
        'phases': phase_rows,
        'exercises': exercise_rows,
        'active_id': active_id,
        'active_phase_id': fase.pk,
        'attempt_id': attempt.pk,
        'xp_total': perfil.xp_total,
        'completed_ids': [item['id'] for item in exercise_rows if item['completed']],
        'urls': {
            'check': reverse('chem1_check_answer', args=[fase.pk]),
            'finish': reverse('chem1_finish_phase', args=[fase.pk]),
            'map': reverse('trilha', args=[fase.modulo.disciplina_id]),
        },
    }
    context = contexto_papel(request)
    context.update({'fase': fase, 'perfil': perfil, 'tema_aplicado': perfil.tema_fundo if papel_efetivo(request) == 'aluno' else fase.modulo.disciplina.tema, 'aparencia_interface': perfil.aparencia_interface, 'chem1_payload': safe_payload})
    return render(request, 'curriculo/chem1_player.html', context)


@login_required
@require_POST
def chem1_check_answer(request,fase_id):
    fase=get_object_or_404(Fase,pk=fase_id,modulo__disciplina__slug='quimica-1')
    aid=request.session.get('chem1_attempt_id')
    if not aid or request.session.get('chem1_phase_id')!=fase.pk: return JsonResponse({'error':'Tentativa não encontrada. Reabra a fase.'},status=409)
    attempt=get_object_or_404(TentativaFase,pk=aid,perfil__usuario=request.user,fase=fase,finalizada_em__isnull=True)
    try:
        payload=json.loads(request.body or '{}'); q=get_object_or_404(Questao,pk=int(payload['questao_id']),fase=fase)
        data=q.dados_dinamicos; answer=data['challenge']['answer']; specs=data.get('simulation',{}).get('parameters',[])
        allowed={s['key']:s for s in specs}; supplied=payload.get('parameters') or {}
        if set(supplied)-set(allowed): return JsonResponse({'error':'Parâmetro desconhecido.'},status=400)
        params={k:float(supplied.get(k,s['value'])) for k,s in allowed.items()}
        for k,v in params.items():
            s=allowed[k]
            if not s['min']<=v<=s['max']: return JsonResponse({'error':f'Parâmetro fora do limite: {k}.'},status=400)
            step=(v-float(s['min']))/float(s['step'])
            if abs(step-round(step))>1e-6: return JsonResponse({'error':f'Incremento inválido: {k}.'},status=400)
        kind=answer['type']; chosen=None; expected=None
        if kind=='choice':
            chosen=get_object_or_404(Opcao,pk=int(payload['option_id']),questao=q); correct=chosen.e_correta
            submitted={'option_id':chosen.pk,'text':chosen.texto}; right=q.opcoes.filter(e_correta=True).first()
            snapshot={'option_id':right.pk,'text':right.texto} if right else {}
        elif kind=='dynamic_choice':
            submitted_value=str(payload.get('value','')); expected=calculate(answer['formula'],params)
            valid={str(x.get('value')) for x in answer.get('choices',[]) if isinstance(x,dict)}
            if submitted_value not in valid: return JsonResponse({'error':'Alternativa inválida.'},status=400)
            correct=is_correct(submitted_value,expected); submitted={'value':submitted_value}; snapshot={'value':expected}
        else:
            submitted_value=payload.get('value')
            if submitted_value is None: return JsonResponse({'error':'Informe um valor.'},status=400)
            expected=calculate(answer['formula'],params)
            correct=is_correct(submitted_value,expected,answer.get('tolerance',0))
            submitted={'value':submitted_value,'unit':answer.get('unit','')}; snapshot={'value':expected,'unit':answer.get('unit','')}
        feedback=answer.get('explanation',answer.get('solution','Resposta correta.')) if correct else answer.get('hint','Revise a simulação e tente novamente.')
        with transaction.atomic():
            RespostaTentativa.objects.update_or_create(tentativa=attempt,questao=q,defaults={'opcao_escolhida':chosen,'texto_questao_snapshot':q.enunciado,'texto_opcao_snapshot':chosen.texto if chosen else '','correta':correct,'tipo_resposta_snapshot':'choice' if kind in {'choice','dynamic_choice'} else 'numeric','resposta_snapshot':submitted,'resposta_correta_snapshot':snapshot,'parametros_snapshot':params,'feedback_snapshot':feedback})
        return JsonResponse({'correct':correct,'feedback':feedback,'hint':'' if correct else answer.get('hint',''),'unit':answer.get('display_unit',answer.get('unit',''))})
    except (KeyError,TypeError,ValueError,ZeroDivisionError) as exc: return JsonResponse({'error':f'Resposta inválida: {exc}'},status=400)

@login_required
@require_POST
@transaction.atomic
def chem1_finish_phase(request,fase_id):
    fase=get_object_or_404(Fase,pk=fase_id,modulo__disciplina__slug='quimica-1'); aid=request.session.get('chem1_attempt_id')
    if not aid or request.session.get('chem1_phase_id')!=fase.pk: return JsonResponse({'error':'Tentativa não encontrada.'},status=409)
    attempt=get_object_or_404(TentativaFase.objects.select_for_update(),pk=aid,perfil__usuario=request.user,fase=fase)
    if attempt.finalizada_em: return JsonResponse({'status':'ok','aprovado':attempt.aprovado,'moedas_ganhas':attempt.moedas_ganhas,'xp_ganho':attempt.xp_ganho})
    answers=list(attempt.respostas.select_related('questao').all()); correct=sum(a.correta for a in answers); approved=len(answers)==1 and correct==1; percent=Decimal(correct*100)
    xp=int(answers[0].questao.dados_dinamicos.get('completion',{}).get('xp',fase.xp_recompensa)) if approved else 0
    attempt.acertos=correct; attempt.erros=max(0,len(answers)-correct); attempt.aproveitamento=percent; attempt.aprovado=approved; attempt.xp_ganho=xp; attempt.finalizada_em=timezone.now()
    attempt.save(update_fields=['acertos','erros','aproveitamento','aprovado','xp_ganho','finalizada_em'])
    coins=conceder_moedas_por_questao(attempt,answers) if approved else 0
    if approved: attempt.perfil.xp_total+=xp; attempt.perfil.save(update_fields=['xp_total'])
    progress,_=ProgressoFase.objects.get_or_create(perfil=attempt.perfil,fase=fase)
    progress.tentativas+=1; progress.erros+=attempt.erros; progress.data_ultima_tentativa=timezone.now(); progress.melhor_aproveitamento=max(progress.melhor_aproveitamento,percent)
    if approved: progress.concluida=True; progress.data_conclusao=timezone.now()
    progress.save(); request.session.pop('chem1_attempt_id',None); request.session.pop('chem1_phase_id',None)
    return JsonResponse({'status':'ok','aprovado':approved,'acertos':correct,'erros':attempt.erros,'total':1,'aproveitamento':float(percent),'xp_ganho':xp,'moedas_ganhas':coins})
