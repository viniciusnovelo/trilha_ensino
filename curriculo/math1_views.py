"""Player e endpoints de Matemática 1."""
import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Fase, Questao, Opcao, Disciplina
from .rewards import conceder_moedas_por_questao
from .views import fase_esta_liberada, contexto_papel, papel_efetivo
from .math1_engine import calculate, is_correct
from gamificacao.models import PerfilUsuario, TentativaFase, RespostaTentativa, ProgressoFase
from gamificacao.vidas import registrar_resposta_com_vida

@login_required
@ensure_csrf_cookie
def math1_player(request, fase_id):
    fase = get_object_or_404(Fase.objects.select_related("modulo__disciplina"), pk=fase_id, modulo__disciplina__slug="matematica-1")
    if not fase_esta_liberada(request, fase): return redirect('trilha', trilha_id=fase.modulo.disciplina_id)
    question = get_object_or_404(Questao.objects.prefetch_related("opcoes"), fase=fase)
    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=request.user)
    if papel_efetivo(request) == 'aluno' and perfil.vidas <= 0 and not ProgressoFase.objects.filter(perfil=perfil, fase=fase, concluida=True).exists():
        return redirect('trilha', trilha_id=fase.modulo.disciplina_id)
    attempt = TentativaFase.objects.create(perfil=perfil,fase=fase,fase_titulo_snapshot=fase.titulo,total_questoes=1)
    request.session["math1_attempt_id"], request.session["math1_phase_id"] = attempt.pk, fase.pk
    phases = list(fase.modulo.fases.order_by("ordem","id"))
    order = next((i for i,x in enumerate(phases,1) if x.pk==fase.pk),1)
    all_phases = list(Fase.objects.filter(modulo__disciplina=fase.modulo.disciplina).select_related("modulo").order_by("modulo__ordem","ordem","id"))
    global_index = next((i for i,x in enumerate(all_phases) if x.pk==fase.pk),-1)
    next_phase = all_phases[global_index+1] if 0 <= global_index < len(all_phases)-1 else None
    data = question.dados_dinamicos
    safe_data = json.loads(json.dumps(data))
    safe_answer = safe_data["challenge"]["answer"]
    for private_key in ("correct","formula","tolerance","solution","explanation"):
        safe_answer.pop(private_key, None)
    context = contexto_papel(request)
    options = [{"id":o.pk,"text":o.texto} for o in question.opcoes.all()]
    lab_payload = {
        "phases":[{"number":data["phase"],"title":fase.modulo.titulo,"exercise_ids":[question.codigo_fonte],"exercise_count":1}],
        "exercises":[safe_data],
        "phase":{"id":fase.pk,"title":fase.titulo,"module_title":fase.modulo.titulo,"order":order,"total_phases":len(phases),"next_phase_id":next_phase.pk if next_phase else None,"discipline_id":fase.modulo.disciplina_id},
        "question":{"id":question.pk,"source_id":question.codigo_fonte,"options":options},
    }
    context.update({"fase":fase,"math1_payload":lab_payload})
    return render(request,"curriculo/math1_player.html",context)

@login_required
@require_POST
def math1_check_answer(request, fase_id):
    fase=get_object_or_404(Fase,pk=fase_id,modulo__disciplina__slug="matematica-1")
    if not fase_esta_liberada(request, fase):
        return JsonResponse({'error': 'Esta fase ainda não está liberada.'}, status=403)
    aid=request.session.get("math1_attempt_id")
    if not aid or request.session.get("math1_phase_id") != fase.pk: return JsonResponse({"error":"Tentativa não encontrada. Reabra a fase."},status=409)
    attempt=get_object_or_404(TentativaFase,pk=aid,perfil__usuario=request.user,fase=fase,finalizada_em__isnull=True)
    try:
        payload=json.loads(request.body or "{}")
        question=get_object_or_404(Questao,pk=int(payload["questao_id"]),fase=fase)
        data=question.dados_dinamicos; answer=data["challenge"]["answer"]
        specs=data["simulation"]["parameters"]; allowed={x["key"]:x for x in specs}
        supplied=payload.get("parameters") or {}
        if set(supplied)-set(allowed): return JsonResponse({"error":"Parâmetros desconhecidos."},status=400)
        params={k:float(supplied.get(k,s["value"])) for k,s in allowed.items()}
        for k,v in params.items():
            s=allowed[k]
            if not s["min"] <= v <= s["max"]: return JsonResponse({"error":f"Parâmetro fora do limite: {k}."},status=400)
            steps=(v-float(s["min"]))/float(s["step"])
            if abs(steps-round(steps))>1e-6: return JsonResponse({"error":f"Incremento inválido: {k}."},status=400)
        if question.tipo_resposta=="choice":
            option=get_object_or_404(Opcao,pk=int(payload["opcao_id"]),questao=question)
            correct=bool(option.e_correta); chosen=option
            submitted={"option_id":option.pk,"text":option.texto}
            right=question.opcoes.filter(e_correta=True).first()
            correct_snapshot={"option_id":right.pk,"text":right.texto}
            expected=None; feedback=answer.get("explanation","")
        else:
            submitted_value=float(payload["valor"])
            expected=calculate(answer["formula"],params)
            correct=is_correct(submitted_value,expected,float(answer["tolerance"]))
            chosen=None; submitted={"value":submitted_value,"unit":answer.get("unit","")}
            correct_snapshot={"value":expected,"unit":answer.get("unit","")}
            feedback="Resposta correta." if correct else answer.get("solution","Revise os conceitos e tente novamente.")
        with transaction.atomic():
            resposta_salva, vidas_atualizadas, resposta_criada, sem_vidas = registrar_resposta_com_vida(
            attempt, question, {
                "opcao_escolhida":chosen,"texto_questao_snapshot":question.enunciado,
                "texto_opcao_snapshot":chosen.texto if chosen else "","correta":correct,
                "tipo_resposta_snapshot":question.tipo_resposta,"resposta_snapshot":submitted,
                "resposta_correta_snapshot":correct_snapshot,"parametros_snapshot":params,"feedback_snapshot":feedback
            },
            consumir_vida=(papel_efetivo(request) == 'aluno'),
        )
        if sem_vidas:
            return JsonResponse({'error': 'Você está sem vidas. Aguarde a recuperação ou consulte a loja.', 'vidas': vidas_atualizadas, 'resposta_ja_registrada': not resposta_criada}, status=409)
        correct = resposta_salva.correta
        feedback = resposta_salva.feedback_snapshot
        return JsonResponse({"correct":correct,"feedback":feedback, 'solution': answer.get('solution') or answer.get('explanation') or feedback,"hint":"" if correct else answer.get("hint",""),
            "expected_display":None if expected is None else round(expected,int(answer.get("digits",2))),
            "unit":answer.get("display_unit",answer.get("unit","")), 'vidas': vidas_atualizadas, 'resposta_ja_registrada': not resposta_criada})
    except (KeyError,TypeError,ValueError,ZeroDivisionError) as exc:
        return JsonResponse({"error":f"Resposta inválida: {exc}"},status=400)

@login_required
@require_POST
@transaction.atomic
def math1_finish_phase(request, fase_id):
    fase=get_object_or_404(Fase,pk=fase_id,modulo__disciplina__slug="matematica-1")
    aid=request.session.get("math1_attempt_id")
    if not fase_esta_liberada(request, fase):
        return JsonResponse({'error': 'Esta fase ainda não está liberada.'}, status=403)
    if not aid or request.session.get("math1_phase_id")!=fase.pk:
        return JsonResponse({"error":"Tentativa não encontrada."},status=409)
    attempt=get_object_or_404(
        TentativaFase.objects.select_for_update(),
        pk=aid,perfil__usuario=request.user,fase=fase,
    )
    if attempt.finalizada_em:
        return JsonResponse({
            "status":"ok","aprovado":attempt.aprovado,
            "moedas_ganhas":attempt.moedas_ganhas,
        })
    answers=list(attempt.respostas.select_related("questao").all())
    correct=sum(x.correta for x in answers)
    percent=Decimal(correct*100)
    approved=len(answers)==1 and correct==1
    xp=0
    if approved and answers[0].questao_id:
        xp=int(answers[0].questao.dados_dinamicos.get("completion",{}).get("xp",30))
    attempt.acertos=correct
    attempt.erros=max(0,len(answers)-correct)
    attempt.aproveitamento=percent
    attempt.aprovado=approved
    attempt.xp_ganho=xp
    attempt.finalizada_em=timezone.now()
    attempt.save(update_fields=[
        "acertos","erros","aproveitamento","aprovado","xp_ganho","finalizada_em",
    ])
    moedas=0
    if approved:
        moedas=conceder_moedas_por_questao(attempt,answers)
        perfil=attempt.perfil
        perfil.xp_total+=xp
        perfil.save(update_fields=["xp_total"])
    progress,_=ProgressoFase.objects.get_or_create(perfil=attempt.perfil,fase=fase)
    progress.tentativas+=1
    progress.erros+=attempt.erros
    progress.data_ultima_tentativa=timezone.now()
    progress.melhor_aproveitamento=max(progress.melhor_aproveitamento,percent)
    if approved:
        progress.concluida=True
        progress.data_conclusao=timezone.now()
    progress.save()
    request.session.pop("math1_attempt_id",None)
    request.session.pop("math1_phase_id",None)
    return JsonResponse({
        "status":"ok","aprovado":approved,"acertos":correct,
        "erros":attempt.erros,"total":1,"aproveitamento":float(percent),
        "xp_ganho":xp,"moedas_ganhas":moedas,
    })
