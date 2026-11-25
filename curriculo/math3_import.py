"""Validação e importação idempotente do Matemática 3; preserva os dados de origem."""
from collections import defaultdict
from django.db import transaction
from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from .math3_engine import FORMULAS

ANSWER_TYPES = {"choice", "dynamic_choice", "numeric", "pair_numeric"}

def validate_math3_source(data):
    module = data.get("module", {})
    if module.get("module_number") != 3 or module.get("subject") != "Matemática":
        raise ValueError("A fonte não corresponde ao Matemática 3.")
    phases = {p["number"]: p for p in data.get("phases", [])}
    exercises = data.get("exercises", [])
    if len(phases) != 3 or len(exercises) != 24:
        raise ValueError("Matemática 3 deve conter 3 fases e 24 exercícios.")
    grouped, ids = defaultdict(list), set()
    for ex in exercises:
        if ex["id"] in ids or ex["phase"] not in phases:
            raise ValueError(f"ID duplicado ou fase inválida: {ex.get('id')}")
        ids.add(ex["id"])
        grouped[ex["phase"]].append(ex)
    expected_ids = set()
    for number, phase in phases.items():
        if len(grouped[number]) != phase["exercise_count"] or {e["id"] for e in grouped[number]} != set(phase["exercise_ids"]):
            raise ValueError(f"Manifesto inconsistente na fase {number}.")
        expected_ids.update(phase["exercise_ids"])
    if ids != expected_ids:
        raise ValueError("Os IDs dos exercícios não correspondem ao manifesto.")
    for ex in exercises:
        answer = ex["challenge"]["answer"]
        kind = answer.get("type")
        if kind not in ANSWER_TYPES:
            raise ValueError(f"Tipo de resposta desconhecido em {ex['id']}: {kind}")
        specs = ex.get("simulation", {}).get("parameters", [])
        keys = [p["key"] for p in specs]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Parâmetros duplicados em {ex['id']}.")
        for spec in specs:
            if spec["step"] <= 0 or spec["min"] > spec["max"] or not spec["min"] <= spec["value"] <= spec["max"]:
                raise ValueError(f"Faixa de parâmetro inválida em {ex['id']}: {spec['key']}.")
        if kind in {"numeric", "pair_numeric", "dynamic_choice"}:
            formula = answer.get("formula")
            if formula not in FORMULAS:
                raise ValueError(f"Fórmula sem implementação em {ex['id']}: {formula}")
            if not specs:
                raise ValueError(f"Resposta dinâmica sem parâmetros em {ex['id']}.")
        if kind in {"choice", "dynamic_choice"}:
            choices = answer.get("choices", [])
            if not choices:
                raise ValueError(f"Sem alternativas em {ex['id']}.")
            if kind == "choice" and not 0 <= int(answer["correct"]) < len(choices):
                raise ValueError(f"Gabarito inválido em {ex['id']}.")
        if kind == "pair_numeric":
            components = answer.get("components", [])
            if len(components) != 2 or len({c["key"] for c in components}) != 2:
                raise ValueError(f"Resposta em pares inválida em {ex['id']}.")
    return phases, grouped

@transaction.atomic
def import_math3_game(data):
    phases, grouped = validate_math3_source(data)
    materia, _ = Materia.objects.get_or_create(
        slug="matematica",
        defaults={"nome": "Matemática", "descricao": "Jogos de Matemática", "icone": "calculator", "ordem": 2, "ativo": True},
    )
    game, _ = Disciplina.objects.get_or_create(
        slug="matematica-3",
        defaults={"nome": "Matemática 3", "descricao": data["module"].get("description", ""), "materia": materia, "icone": "calculator", "ordem": 3, "ativo": False},
    )
    total = 0
    for number, topic_data in sorted(phases.items()):
        topic, _ = Modulo.objects.update_or_create(
            disciplina=game, ordem=number,
            defaults={"titulo": topic_data["title"], "descricao": topic_data.get("description", "")},
        )
        for order, exercise in enumerate(grouped[number], 1):
            answer = exercise["challenge"]["answer"]
            phase, _ = Fase.objects.update_or_create(
                modulo=topic, ordem=order,
                defaults={"titulo": exercise["title"][:150], "tipo": "quiz", "xp_recompensa": int(exercise.get("completion", {}).get("xp", 30)), "moedas_recompensa": 0, "deslocamento_y": 0},
            )
            dynamic = {**exercise, "source_math_module": 3, "source_exercise_id": exercise["id"]}
            question, _ = Questao.objects.update_or_create(
                codigo_fonte=exercise["id"],
                defaults={"fase": phase, "enunciado": exercise["challenge"]["prompt"], "explicacao_erro": answer.get("explanation", answer.get("solution", "")), "tipo_resposta": ("choice" if answer["type"] in {"choice", "dynamic_choice"} else "numeric"), "dados_dinamicos": dynamic},
            )
            if answer["type"] == "choice":
                for index, option in enumerate(answer["choices"], 1):
                    Opcao.objects.update_or_create(questao=question, ordem=index, defaults={"texto": option, "e_correta": index - 1 == answer["correct"]})
            elif answer["type"] == "dynamic_choice":
                for index, option in enumerate(answer["choices"], 1):
                    label = option["label"] if isinstance(option, dict) else str(option)
                    Opcao.objects.update_or_create(questao=question, ordem=index, defaults={"texto": label, "e_correta": False})
            total += 1
    return {"game": game.nome, "topics": len(phases), "questions": total, "disciplina_id": game.pk}
