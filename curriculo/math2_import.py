"""Importador idempotente do jogo Matemática 2."""
from collections import defaultdict
from django.db import transaction
from .models import Materia,Disciplina,Modulo,Fase,Questao,Opcao
from .math2_engine import FORMULAS
def validate_math2_source(data):
    if data.get("module",{}).get("module_number")!=2 or data.get("module",{}).get("subject")!="Matemática": raise ValueError("Fonte não corresponde ao Matemática 2.")
    phases={p["number"]:p for p in data["phases"]}; exercises=data["exercises"]
    if len(phases)!=5 or len(exercises)!=39: raise ValueError("Matemática 2 deve conter 5 tópicos e 39 exercícios.")
    ids=set(); grouped=defaultdict(list)
    for ex in exercises:
        if ex["id"] in ids or ex["phase"] not in phases: raise ValueError(f"ID duplicado ou tópico inválido: {ex.get('id')}")
        ids.add(ex["id"]); grouped[ex["phase"]].append(ex)
    for no,t in phases.items():
        if len(grouped[no])!=t["exercise_count"] or set(t["exercise_ids"])!={e["id"] for e in grouped[no]}: raise ValueError(f"Manifesto inconsistente no tópico {no}.")
    expected_ids={eid for topic in phases.values() for eid in topic["exercise_ids"]}
    if ids != expected_ids:
        raise ValueError("Os IDs dos exercícios não correspondem ao manifesto dos tópicos.")
    for ex in exercises:
        a=ex["challenge"]["answer"]
        specs=ex.get("simulation",{}).get("parameters",[])
        keys={p["key"] for p in specs}
        if len(keys)!=len(specs):
            raise ValueError(f"Parâmetros duplicados em {ex['id']}.")
        for spec in specs:
            if spec["step"] <= 0 or spec["min"] > spec["max"] or not spec["min"] <= spec["value"] <= spec["max"]:
                raise ValueError(f"Faixa de parâmetro inválida em {ex['id']}: {spec['key']}.")
        if a["type"]=="numeric":
            if a.get("formula") not in FORMULAS:
                raise ValueError(f"Fórmula sem implementação em {ex['id']}: {a.get('formula')}")
            if not specs:
                raise ValueError(f"Exercício numérico sem parâmetros em {ex['id']}.")
        elif a["type"]=="choice":
            opts=a.get("choices",a.get("options",[]))
            if not opts or not 0<=int(a["correct"])<len(opts):
                raise ValueError(f"Gabarito inválido em {ex['id']}.")
        else:
            raise ValueError(f"Tipo de resposta desconhecido em {ex['id']}: {a['type']}.")
    return phases,grouped
@transaction.atomic
def import_math2_game(data):
    phases,grouped=validate_math2_source(data)
    materia,_=Materia.objects.update_or_create(slug="matematica",defaults={"nome":"Matemática","descricao":"Jogos de Matemática","icone":"calculator","ordem":2,"ativo":True})
    game,_=Disciplina.objects.update_or_create(slug="matematica-2",defaults={"nome":"Matemática 2","descricao":data["module"].get("description",""),"materia":materia,"icone":"calculator","ordem":2,"ativo":True,"autor":None})
    total=0
    for no,t in sorted(phases.items()):
        topic,_=Modulo.objects.update_or_create(disciplina=game,ordem=no,defaults={"titulo":t["title"],"descricao":t.get("description","")})
        for order,ex in enumerate(grouped[no],1):
            a=ex["challenge"]["answer"]; dynamic={**ex,"source_math_module":2,"source_exercise_id":ex["id"]}
            phase,_=Fase.objects.update_or_create(modulo=topic,ordem=order,defaults={"titulo":ex["title"][:150],"tipo":"quiz","xp_recompensa":int(ex.get("completion",{}).get("xp",30)),"moedas_recompensa":0,"deslocamento_y":0})
            q,_=Questao.objects.update_or_create(codigo_fonte=ex["id"],defaults={"fase":phase,"enunciado":ex["challenge"]["prompt"],"explicacao_erro":a.get("explanation",a.get("solution","")),"tipo_resposta":a["type"],"dados_dinamicos":dynamic})
            if a["type"]=="choice":
                opts=a.get("choices",a.get("options",[]))
                for i,texto in enumerate(opts,1):
                    Opcao.objects.update_or_create(
                        questao=q, ordem=i,
                        defaults={"texto":texto,"e_correta":i-1==a["correct"]},
                    )
            total+=1
    return {"game":game.nome,"topics":len(phases),"phases":total,"questions":total,"disciplina_id":game.pk}
