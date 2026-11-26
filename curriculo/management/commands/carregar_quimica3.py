import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculo.chem3_engine import FORMULAS
from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao


class Command(BaseCommand):
    help = "Valida ou importa os módulos e exercícios da Química 3."

    def add_arguments(self, parser):
        parser.add_argument("--arquivo", default="modulo3_quimica.json")
        parser.add_argument("--exercicios-dir", default="exercicios")
        parser.add_argument("--simulador", default="fontes/quimica3/index.html")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida JSON, manifesto, exercícios individuais e cenas sem alterar o banco.",
        )

    def _load_json(self, path, label):
        if not path.is_file():
            raise CommandError(f"{label} não encontrado: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"{label} inválido ({path}): {exc}")

    def _validate(self, data, exercises_dir, simulator_path):
        if not isinstance(data, dict) or not isinstance(data.get("module"), dict):
            raise CommandError("Estrutura inválida: objeto 'module' ausente.")
        if data["module"].get("module_number") != 3:
            raise CommandError("O JSON não identifica o módulo como Química 3.")

        phases = data.get("phases")
        exercises = data.get("exercises")
        if not isinstance(phases, list) or not isinstance(exercises, list):
            raise CommandError("O JSON precisa conter as listas 'phases' e 'exercises'.")
        if len(phases) != 5:
            raise CommandError(f"Esperadas 5 fases; encontradas {len(phases)}.")
        if len(exercises) != 38:
            raise CommandError(f"Esperados 38 exercícios; encontrados {len(exercises)}.")

        phase_numbers = [p.get("number") for p in phases]
        if len(set(phase_numbers)) != len(phase_numbers):
            raise CommandError("Há números de fase duplicados.")
        if sorted(phase_numbers) != [1, 2, 3, 4, 5]:
            raise CommandError("A numeração das fases deve ser de 1 a 5.")

        by_id = {}
        for exercise in exercises:
            exercise_id = exercise.get("id")
            if not exercise_id or exercise_id in by_id:
                raise CommandError(f"ID de exercício ausente ou duplicado: {exercise_id!r}.")
            by_id[exercise_id] = exercise
            if exercise.get("phase") not in phase_numbers:
                raise CommandError(f"{exercise_id}: fase inexistente.")
            if not isinstance(exercise.get("exercise_number"), int):
                raise CommandError(f"{exercise_id}: número do exercício inválido.")
            try:
                answer = exercise["challenge"]["answer"]
                answer_type = answer["type"]
                scene = exercise["simulation"]["scene"]
                parameters = exercise["simulation"].get("parameters", [])
            except (KeyError, TypeError) as exc:
                raise CommandError(f"{exercise_id}: estrutura de desafio/simulação incompleta ({exc}).")
            if answer_type not in {"choice", "dynamic_choice", "numeric", "pair_numeric"}:
                raise CommandError(f"{exercise_id}: tipo de resposta não suportado: {answer_type}.")
            if answer_type != "choice" and answer.get("formula") not in FORMULAS:
                raise CommandError(
                    f"{exercise_id}: fórmula não cadastrada no motor: {answer.get('formula')!r}."
                )
            if not isinstance(parameters, list):
                raise CommandError(f"{exercise_id}: parâmetros da simulação devem ser uma lista.")
            keys = set()
            for spec in parameters:
                try:
                    key = spec["key"]
                    minimum, maximum, step, value = (
                        float(spec["min"]), float(spec["max"]),
                        float(spec["step"]), float(spec["value"]),
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise CommandError(f"{exercise_id}: parâmetro inválido ({exc}).")
                if key in keys:
                    raise CommandError(f"{exercise_id}: parâmetro duplicado: {key}.")
                keys.add(key)
                if step <= 0 or minimum > maximum or not minimum <= value <= maximum:
                    raise CommandError(f"{exercise_id}: limites/valor inválidos no parâmetro {key}.")
            if answer_type in {"choice", "dynamic_choice"}:
                choices = answer.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise CommandError(f"{exercise_id}: lista de alternativas vazia.")
                if answer_type == "choice" and not 0 <= int(answer.get("correct", -1)) < len(choices):
                    raise CommandError(f"{exercise_id}: índice da alternativa correta inválido.")
                if answer_type == "dynamic_choice":
                    if not all(isinstance(item, dict) and "value" in item and "label" in item for item in choices):
                        raise CommandError(f"{exercise_id}: alternativas dinâmicas inválidas.")
            if answer_type == "pair_numeric" and not answer.get("components"):
                raise CommandError(f"{exercise_id}: questão pair_numeric sem componentes.")

        for phase in phases:
            ids = phase.get("exercise_ids", [])
            expected = [e["id"] for e in exercises if e["phase"] == phase["number"]]
            if phase.get("exercise_count") != len(ids) or ids != expected:
                raise CommandError(
                    f"Fase {phase['number']}: exercise_ids/count não correspondem aos exercícios do JSON."
                )
            if any(exercise_id not in by_id for exercise_id in ids):
                raise CommandError(f"Fase {phase['number']}: referência a exercício inexistente.")

        manifest_path = exercises_dir / "manifest_quimica3.json"
        manifest = self._load_json(manifest_path, "Manifesto")
        manifest_items = manifest.get("exercises", [])
        if manifest.get("exercise_count") != len(exercises) or len(manifest_items) != len(exercises):
            raise CommandError("Manifesto: quantidade de exercícios divergente.")
        manifest_by_id = {item.get("id"): item for item in manifest_items}
        if len(manifest_by_id) != len(manifest_items) or set(manifest_by_id) != set(by_id):
            raise CommandError("Manifesto: IDs ausentes, extras ou duplicados.")

        checked = 0
        for exercise_id, exercise in by_id.items():
            item = manifest_by_id[exercise_id]
            relative = Path(item.get("path", ""))
            if relative.is_absolute() or ".." in relative.parts:
                raise CommandError(f"{exercise_id}: caminho inseguro no manifesto.")
            individual = self._load_json(exercises_dir.parent / relative, f"Exercício {exercise_id}")
            if individual != exercise:
                raise CommandError(f"{exercise_id}: divergência entre JSON principal e arquivo individual.")
            if item.get("phase") != exercise["phase"] or item.get("title") != exercise["title"]:
                raise CommandError(f"{exercise_id}: metadados divergentes no manifesto.")
            checked += 1

        simulator = self._load_text(simulator_path, "Simulador-fonte")
        scenes = {e["simulation"]["scene"] for e in exercises}
        missing_scenes = sorted(scene for scene in scenes if scene not in simulator)
        if missing_scenes:
            raise CommandError("Cenas ausentes no simulador-fonte: " + ", ".join(missing_scenes))

        return {
            "phases": len(phases),
            "exercises": len(exercises),
            "individuals": checked,
            "scenes": len(scenes),
            "types": sorted({e["challenge"]["answer"]["type"] for e in exercises}),
        }

    def _load_text(self, path, label):
        if not path.is_file():
            raise CommandError(f"{label} não encontrado: {path}")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandError(f"Não foi possível ler {label}: {exc}")

    def handle(self, *args, **options):
        source_path = Path(options["arquivo"])
        exercises_dir = Path(options["exercicios_dir"])
        simulator_path = Path(options["simulador"])
        data = self._load_json(source_path, "JSON principal")
        report = self._validate(data, exercises_dir, simulator_path)

        self.stdout.write(
            self.style.SUCCESS(
                "Validação aprovada: "
                f'{report["phases"]} fases, {report["exercises"]} exercícios, '
                f'{report["individuals"]} arquivos individuais, {report["scenes"]} cenas.'
            )
        )
        self.stdout.write("Tipos de questão: " + ", ".join(report["types"]))
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("DRY-RUN: nenhuma alteração foi feita no banco."))
            return

        with transaction.atomic():
            quimica1 = Disciplina.objects.filter(slug="quimica-2").first()
            materia = (
                (quimica1.materia if quimica1 else None)
                or Materia.objects.filter(slug__icontains="quim").first()
            )
            if materia is None:
                materia = Materia.objects.create(
                    nome="Química", slug="quimica", ordem=2, ativo=True
                )

            disciplina, _ = Disciplina.objects.get_or_create(
                slug="quimica-3",
                defaults={
                    "nome": data["module"].get("title", "Química 3"),
                    "descricao": data["module"].get("description", ""),
                    "materia": materia,
                    "autor": quimica1.autor if quimica1 else None,
                    "tema": quimica1.tema if quimica1 else "tema-padrao",
                    "ordem": 3,
                    "ativo": quimica1.ativo if quimica1 else False,
                },
            )
            disciplina.nome = data["module"].get("title", "Química 3")
            disciplina.descricao = data["module"].get("description", "")
            disciplina.materia = materia
            if quimica1:
                disciplina.autor = quimica1.autor
                disciplina.tema = quimica1.tema
                disciplina.ativo = quimica1.ativo
            disciplina.save()

            for phase in data["phases"]:
                module, _ = Modulo.objects.update_or_create(
                    disciplina=disciplina,
                    ordem=phase["number"],
                    defaults={
                        "titulo": phase["title"],
                        "descricao": phase.get("description", ""),
                    },
                )
                phase_exercises = [
                    exercise for exercise in data["exercises"]
                    if exercise["phase"] == phase["number"]
                ]
                for exercise in phase_exercises:
                    phase_obj, _ = Fase.objects.update_or_create(
                        modulo=module,
                        ordem=exercise["exercise_number"],
                        defaults={
                            "titulo": exercise["title"],
                            "tipo": "quiz",
                            "xp_recompensa": exercise.get("completion", {}).get("xp", 30),
                        },
                    )
                    answer = exercise["challenge"]["answer"]
                    question, _ = Questao.objects.update_or_create(
                        codigo_fonte=exercise["id"],
                        defaults={
                            "fase": phase_obj,
                            "enunciado": exercise["challenge"]["prompt"],
                            "explicacao_erro": answer.get("hint", ""),
                            "tipo_resposta": "choice" if answer["type"] == "choice" else "numeric",
                            "dados_dinamicos": exercise,
                        },
                    )
                    if answer["type"] == "choice":
                        choices = answer.get("choices", [])
                        existing = list(question.opcoes.order_by("ordem", "id"))
                        for index, choice_text in enumerate(choices):
                            if index < len(existing):
                                option = existing[index]
                                option.texto = choice_text
                                option.e_correta = index == answer["correct"]
                                option.ordem = index + 1
                                option.save()
                            else:
                                Opcao.objects.create(
                                    questao=question,
                                    texto=choice_text,
                                    e_correta=index == answer["correct"],
                                    ordem=index + 1,
                                )
                        for option in existing[len(choices):]:
                            option.delete()
                    elif question.opcoes.exists():
                        question.opcoes.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Química 3 importada: {report["phases"]} fases e '
                f'{report["exercises"]} exercícios. Nenhum outro módulo foi removido.'
            )
        )
