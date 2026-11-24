"""Importação oficial de Física no formato jogo -> tópicos -> fases de uma questão."""
from __future__ import annotations

from collections import defaultdict

from django.db import transaction

from .models import Materia, Disciplina, Modulo, Fase, Questao, Opcao


GAME_SLUGS = {1: "fisica-1", 2: "fisica-2", 3: "fisica-3"}


@transaction.atomic
def import_physics_game(data: dict, game_number: int, summary: dict) -> dict:
    if game_number not in GAME_SLUGS:
        raise ValueError("Número de jogo de Física inválido.")
    if data.get("module") != game_number:
        raise ValueError("A fonte JSON não corresponde ao jogo solicitado.")

    phases = {phase["number"]: phase for phase in data["phases"]}
    grouped = defaultdict(list)
    for exercise in data["exercises"]:
        if exercise.get("phase") not in phases:
            raise ValueError(f"Tópico inválido em {exercise.get('id')}.")
        grouped[exercise["phase"]].append(exercise)

    materia, _ = Materia.objects.update_or_create(
        slug="fisica",
        defaults={
            "nome": "Física",
            "descricao": "Jogos de Física 1, Física 2 e Física 3",
            "icone": "atom",
            "ordem": 1,
            "ativo": True,
        },
    )
    game, _ = Disciplina.objects.update_or_create(
        slug=GAME_SLUGS[game_number],
        defaults={
            "nome": f"Física {game_number}",
            "descricao": data.get("title", ""),
            "materia": materia,
            "icone": "atom",
            "ordem": game_number,
            "ativo": True,
            "autor": None,
        },
    )

    total_questions = 0
    total_topics = 0
    for topic_number, topic_data in sorted(phases.items()):
        topic, _ = Modulo.objects.update_or_create(
            disciplina=game,
            ordem=topic_number,
            defaults={
                "titulo": topic_data["title"],
                "descricao": data.get("title", ""),
            },
        )
        total_topics += 1

        for order, exercise in enumerate(grouped[topic_number], start=1):
            answer = exercise["challenge"]["answer"]
            kind = answer["type"]
            dynamic = {
                **exercise,
                "source_schema_version": data.get("schema_version"),
                "source_constants": data.get("constants", {}),
                "source_module": game_number,
                "source_phase_id": topic_data["id"],
                "source_phase_metadata": topic_data,
                "source_exercise_id": exercise["id"],
            }
            phase, _ = Fase.objects.update_or_create(
                modulo=topic,
                ordem=order,
                defaults={
                    "titulo": (exercise.get("title") or f"Questão {order}")[:150],
                    "tipo": "quiz",
                    "xp_recompensa": 0,
                    "moedas_recompensa": 0,
                    "deslocamento_y": 0,
                },
            )
            question, _ = Questao.objects.update_or_create(
                codigo_fonte=exercise["id"],
                defaults={
                    "fase": phase,
                    "enunciado": exercise["challenge"]["prompt"],
                    "explicacao_erro": answer.get(
                        "explanation",
                        answer.get("solution", ""),
                    ),
                    "tipo_resposta": kind,
                    "dados_dinamicos": dynamic,
                },
            )
            question.opcoes.all().delete()
            if kind == "choice":
                choices = answer.get("choices", answer.get("options", []))
                Opcao.objects.bulk_create([
                    Opcao(
                        questao=question,
                        texto=label,
                        e_correta=(index == answer["correct"]),
                        ordem=index + 1,
                    )
                    for index, label in enumerate(choices)
                ])
            total_questions += 1

    return {
        **summary,
        "materia_id": materia.pk,
        "disciplina_id": game.pk,
        "game": game.nome,
        "topics": total_topics,
        "phases": total_questions,
        "questions": total_questions,
    }
