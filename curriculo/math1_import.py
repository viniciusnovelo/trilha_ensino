"""Importador idempotente do jogo Matemática 1."""
from collections import defaultdict
from django.db import transaction
from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from .math1_engine import FORMULAS

def validate_math1_source(data):
    if data.get("module", {}).get("module_number") != 1 or data.get("module", {}).get("subject") != "Matemática":
        raise ValueError("A fonte não corresponde ao Matemática 1.")
    phases = {p["number"]: p for p in data["phases"]}
    if len(phases) != 5 or len(data["exercises"]) != 35:
        raise ValueError("Matemática 1 deve conter 5 tópicos e 35 exercícios.")
    ids = set()
    grouped = defaultdict(list)
    for ex in data["exercises"]:
        if ex["id"] in ids or ex["phase"] not in phases:
            raise ValueError(f"ID duplicado ou tópico inválido: {ex.get('id')}")
        ids.add(ex["id"])
        grouped[ex["phase"]].append(ex)
    for phase_no, topic in phases.items():
        if len(grouped[phase_no]) != topic["exercise_count"] or set(topic["exercise_ids"]) != {e["id"] for e in grouped[phase_no]}:
            raise ValueError(f"Manifesto inconsistente no tópico {phase_no}.")
    for ex in data["exercises"]:
        answer = ex["challenge"]["answer"]
        if answer["type"] == "numeric" and answer.get("formula") not in FORMULAS:
            raise ValueError(f"Fórmula sem implementação em {ex['id']}: {answer.get('formula')}")
    return phases, grouped


@transaction.atomic
def import_math1_game(data):
    phases, grouped = validate_math1_source(data)
    materia, _ = Materia.objects.update_or_create(slug="matematica", defaults={
        "nome":"Matemática", "descricao":"Jogos de Matemática", "icone":"calculator", "ordem":2, "ativo":True
    })
    game, _ = Disciplina.objects.update_or_create(slug="matematica-1", defaults={
        "nome":"Matemática 1", "descricao":data["module"].get("description",""),
        "materia":materia, "icone":"calculator", "ordem":1, "ativo":True, "autor":None
    })
    total = 0
    for number, topic_data in sorted(phases.items()):
        topic, _ = Modulo.objects.update_or_create(disciplina=game, ordem=number, defaults={
            "titulo":topic_data["title"], "descricao":topic_data.get("description","")
        })
        for order, ex in enumerate(grouped[number], 1):
            answer = ex["challenge"]["answer"]
            dynamic = {**ex, "source_math_module":1, "source_exercise_id":ex["id"]}
            phase, _ = Fase.objects.update_or_create(modulo=topic, ordem=order, defaults={
                "titulo":ex["title"][:150], "tipo":"quiz", "xp_recompensa":int(ex.get("completion",{}).get("xp",30)),
                "moedas_recompensa":0, "deslocamento_y":0
            })
            question, _ = Questao.objects.update_or_create(codigo_fonte=ex["id"], defaults={
                "fase":phase, "enunciado":ex["challenge"]["prompt"],
                "explicacao_erro":answer.get("explanation",answer.get("solution","")),
                "tipo_resposta":answer["type"], "dados_dinamicos":dynamic
            })
            question.opcoes.all().delete()
            if answer["type"] == "choice":
                choices = answer.get("choices", answer.get("options", []))
                if not choices or not 0 <= int(answer["correct"]) < len(choices):
                    raise ValueError(f"Gabarito inválido em {ex['id']}.")
                Opcao.objects.bulk_create([Opcao(questao=question,texto=label,e_correta=(i==answer["correct"]),ordem=i+1) for i,label in enumerate(choices)])
            total += 1
    return {"game":game.nome,"topics":len(phases),"phases":total,"questions":total,"disciplina_id":game.pk}
