#!/usr/bin/env python3
"""Reorganiza Física 1/2/3 como jogos, com tópicos e uma questão por fase.

Uso:
    python scripts/reorganizar_jogos_fisica.py --dry-run
    python scripts/reorganizar_jogos_fisica.py --apply

A operação é transacional, idempotente e preserva a árvore antiga como arquivo.
Questões e alternativas existentes são movidas, nunca recriadas ou apagadas.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SOURCE_FILES = {
    1: PROJECT_ROOT / "modulo1_fisica.json",
    2: PROJECT_ROOT / "modulo2_fisica.json",
    3: PROJECT_ROOT / "modulo3_fisica.json",
}

GAME_SLUGS = {
    1: "fisica-1",
    2: "fisica-2",
    3: "fisica-3",
}


def load_sources():
    sources = {}
    for number, path in SOURCE_FILES.items():
        if not path.is_file():
            raise FileNotFoundError(f"Fonte oficial ausente: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("module") != number:
            raise ValueError(f"A fonte {path.name} não corresponde ao jogo Física {number}.")
        phases = data.get("phases")
        exercises = data.get("exercises")
        if not isinstance(phases, list) or not phases:
            raise ValueError(f"{path.name}: fases ausentes.")
        if not isinstance(exercises, list) or not exercises:
            raise ValueError(f"{path.name}: exercícios ausentes.")
        phase_numbers = {item.get("number") for item in phases}
        if len(phase_numbers) != len(phases):
            raise ValueError(f"{path.name}: números de tópicos duplicados.")
        seen = set()
        for exercise in exercises:
            code = exercise.get("id")
            if not code or code in seen:
                raise ValueError(f"{path.name}: código de exercício ausente ou duplicado.")
            if exercise.get("phase") not in phase_numbers:
                raise ValueError(f"{path.name}: tópico inválido em {code}.")
            seen.add(code)
            answer = (exercise.get("challenge") or {}).get("answer") or {}
            if answer.get("type") not in ("choice", "numeric"):
                raise ValueError(f"{path.name}: tipo de resposta inválido em {code}.")
        sources[number] = data
    return sources


def expected_options(exercise):
    answer = exercise["challenge"]["answer"]
    if answer["type"] != "choice":
        return []
    options = answer.get("choices", answer.get("options", []))
    if not isinstance(options, list) or not options:
        raise ValueError(f"Alternativas ausentes em {exercise['id']}.")
    correct_index = answer.get("correct")
    if not isinstance(correct_index, int) or not 0 <= correct_index < len(options):
        raise ValueError(f"Índice da alternativa correta inválido em {exercise['id']}.")
    return [(str(label), index == correct_index) for index, label in enumerate(options)]


def build_plan(sources, Disciplina, Modulo, Fase, Questao, Opcao, Materia):
    materia = Materia.objects.filter(slug="fisica").first()
    if materia is None:
        raise ValueError("A matéria Física (slug=fisica) não existe.")
    legacy = Disciplina.objects.filter(slug="fisica").first()
    if legacy is None:
        raise ValueError("A trilha legada Física (slug=fisica) não existe.")

    plan = []
    all_codes = set()
    for number, data in sources.items():
        phases_by_number = {phase["number"]: phase for phase in data["phases"]}
        grouped = defaultdict(list)
        for exercise in data["exercises"]:
            grouped[exercise["phase"]].append(exercise)

        game = Disciplina.objects.filter(slug=GAME_SLUGS[number]).first()
        if game and game.materia_id != materia.id:
            raise ValueError(f"O slug {GAME_SLUGS[number]} já pertence a outra matéria.")
        topics = []
        for phase_number in sorted(phases_by_number):
            source_phase = phases_by_number[phase_number]
            exercises = sorted(grouped[phase_number], key=lambda item: item["id"])
            topic_module = Modulo.objects.filter(
                disciplina=game, ordem=phase_number
            ).first() if game else None
            topic_phases = []
            for order, exercise in enumerate(exercises, start=1):
                code = exercise["id"]
                if code in all_codes:
                    raise ValueError(f"Código duplicado entre fontes: {code}")
                all_codes.add(code)
                question = Questao.objects.filter(codigo_fonte=code).first()
                if question is None:
                    raise ValueError(f"Questão {code} não está cadastrada no banco.")
                if question.enunciado != exercise["challenge"]["prompt"]:
                    raise ValueError(f"Enunciado divergente para {code}; nada foi alterado.")
                if question.tipo_resposta != exercise["challenge"]["answer"]["type"]:
                    raise ValueError(f"Tipo de resposta divergente para {code}.")
                existing_options = list(
                    question.opcoes.order_by("ordem", "id").values_list("texto", "e_correta")
                )
                if existing_options != expected_options(exercise):
                    raise ValueError(f"Alternativas divergentes para {code}; nada foi alterado.")
                topic_phases.append({
                    "order": order,
                    "exercise": exercise,
                    "question_id": question.pk,
                    "old_phase_id": question.fase_id,
                    "new_phase_id": (
                        Fase.objects.filter(modulo=topic_module, ordem=order)
                        .values_list("id", flat=True).first()
                        if topic_module else None
                    ),
                })
            topics.append({
                "number": phase_number,
                "title": source_phase["title"],
                "description": data.get("title", ""),
                "old_topic_phase_ids": list(
                    Fase.objects.filter(
                        modulo__disciplina=legacy,
                        modulo__ordem=number,
                        ordem=phase_number,
                    ).values_list("id", flat=True)
                ),
                "new_module_id": topic_module.pk if topic_module else None,
                "phases": topic_phases,
            })
        plan.append({
            "number": number,
            "slug": GAME_SLUGS[number],
            "name": f"Física {number}",
            "description": data.get("title", ""),
            "exercise_count": len(data["exercises"]),
            "topic_count": len(data["phases"]),
            "topics": topics,
        })
    return materia, legacy, plan


def apply_plan(materia, legacy, plan, Disciplina, Modulo, Fase, Questao):
    from django.db import transaction
    from django.utils import timezone
    from gamificacao.models import ProgressoFase, RespostaTentativa

    now = timezone.now()
    report = {"games": [], "questions_moved": 0, "progress_rows_created": 0}

    # Keep the old hierarchy available for audit/history; it is hidden from students.
    if legacy.slug == "fisica":
        archived_slug = "fisica-legado"
        collision = Disciplina.objects.filter(slug=archived_slug).exclude(pk=legacy.pk).first()
        if collision:
            raise ValueError("Já existe uma trilha com slug fisica-legado; revisão manual necessária.")
        legacy.slug = archived_slug
        legacy.nome = "Física — estrutura anterior (arquivo)"
        legacy.ativo = False
        legacy.save(update_fields=["slug", "nome", "ativo"])

    for game_data in plan:
        game, _ = Disciplina.objects.update_or_create(
            slug=game_data["slug"],
            defaults={
                "nome": game_data["name"],
                "descricao": game_data["description"],
                "materia": materia,
                "icone": "atom",
                "ordem": game_data["number"],
                "ativo": True,
                "autor": legacy.autor,
                "tema": legacy.tema,
            },
        )
        game_report = {
            "name": game.nome,
            "slug": game.slug,
            "topics": 0,
            "phases": 0,
            "questions": 0,
        }

        for topic in game_data["topics"]:
            module, _ = Modulo.objects.update_or_create(
                disciplina=game,
                ordem=topic["number"],
                defaults={
                    "titulo": topic["title"],
                    "descricao": topic["description"],
                },
            )
            game_report["topics"] += 1
            for phase_data in topic["phases"]:
                exercise = phase_data["exercise"]
                title = exercise.get("title") or f"Questão {phase_data['order']}"
                phase, _ = Fase.objects.update_or_create(
                    modulo=module,
                    ordem=phase_data["order"],
                    defaults={
                        "titulo": title[:150],
                        "tipo": "quiz",
                        "xp_recompensa": 0,
                        "moedas_recompensa": 0,
                        "deslocamento_y": 0,
                    },
                )
                question = Questao.objects.get(pk=phase_data["question_id"])
                if question.fase_id != phase.pk:
                    question.fase = phase
                    question.save(update_fields=["fase"])
                    report["questions_moved"] += 1

                # Rebuild per-question progress from the immutable answer history.
                # Legacy topic-level progress remains intact on the archived phase.
                responses = RespostaTentativa.objects.filter(questao=question)
                by_profile = defaultdict(list)
                for response in responses.select_related("tentativa__perfil").order_by("respondida_em", "id"):
                    by_profile[response.tentativa.perfil_id].append(response)

                for profile_id, answers in by_profile.items():
                    correct_answers = [item for item in answers if item.correta]
                    latest = answers[-1]
                    progress, created = ProgressoFase.objects.get_or_create(
                        perfil_id=profile_id,
                        fase=phase,
                        defaults={
                            "concluida": bool(correct_answers),
                            "erros": sum(1 for item in answers if not item.correta),
                            "tentativas": len(answers),
                            "data_conclusao": correct_answers[-1].respondida_em if correct_answers else None,
                            "melhor_aproveitamento": 100 if correct_answers else 0,
                            "data_ultima_tentativa": latest.respondida_em,
                        },
                    )
                    if created:
                        report["progress_rows_created"] += 1
                    else:
                        # Existing progress is never downgraded by a rerun.
                        if correct_answers and not progress.concluida:
                            progress.concluida = True
                            progress.data_conclusao = correct_answers[-1].respondida_em
                        progress.erros = max(progress.erros, sum(1 for item in answers if not item.correta))
                        progress.tentativas = max(progress.tentativas, len(answers))
                        progress.melhor_aproveitamento = max(progress.melhor_aproveitamento, 100 if correct_answers else 0)
                        progress.data_ultima_tentativa = max(
                            filter(None, [progress.data_ultima_tentativa, latest.respondida_em]),
                            default=None,
                        )
                        progress.save()

                game_report["phases"] += 1
                game_report["questions"] += 1

        report["games"].append(game_report)

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Valida fontes e banco sem gravar alterações.")
    mode.add_argument("--apply", action="store_true", help="Executa a reorganização dentro de uma transação.")
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    from django.db import transaction
    from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao

    sources = load_sources()
    materia, legacy, plan = build_plan(
        sources, Disciplina, Modulo, Fase, Questao, Opcao, Materia
    )
    summary = {
        "status": "dry_run_ok" if args.dry_run else "ready_to_apply",
        "legacy_discipline": {"id": legacy.pk, "slug": legacy.slug},
        "games": [
            {
                "name": game["name"],
                "topics": game["topic_count"],
                "phases": game["exercise_count"],
                "questions": game["exercise_count"],
            }
            for game in plan
        ],
        "total_questions": sum(game["exercise_count"] for game in plan),
        "note": "Questões e alternativas existentes foram conferidas; nenhuma escrita ocorreu no dry-run.",
    }
    if args.apply:
        with transaction.atomic():
            report = apply_plan(materia, legacy, plan, Disciplina, Modulo, Fase, Questao)
        summary.update({"status": "success", **report})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
