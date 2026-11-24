"""Testes da nova hierarquia de jogos de Física."""
import json
from pathlib import Path

from django.test import TestCase

from .models import Disciplina, Fase, Materia, Modulo, Questao
from .physics_game_import import import_physics_game


class PhysicsGameStructureTests(TestCase):
    def setUp(self):
        self.source_path = Path(__file__).resolve().parent.parent / "modulo3_fisica.json"
        self.data = json.loads(self.source_path.read_text(encoding="utf-8"))

    def test_module3_is_imported_as_game_topics_and_single_question_phases(self):
        result = import_physics_game(self.data, 3, {"exercises": 30})

        game = Disciplina.objects.get(slug="fisica-3")
        self.assertEqual(game.nome, "Física 3")
        self.assertEqual(game.materia.slug, "fisica")
        self.assertEqual(game.modulos.count(), 3)
        self.assertEqual(Fase.objects.filter(modulo__disciplina=game).count(), 30)
        self.assertEqual(Questao.objects.filter(fase__modulo__disciplina=game).count(), 30)

        for phase in Fase.objects.filter(modulo__disciplina=game):
            self.assertEqual(
                phase.questoes.count(),
                1,
                msg=f"{phase.titulo} deve possuir exatamente uma questão.",
            )

        self.assertEqual(result["topics"], 3)
        self.assertEqual(result["phases"], 30)
        self.assertEqual(result["questions"], 30)

    def test_all_three_games_keep_official_topic_and_exercise_counts(self):
        expected = {
            1: (4, 28),
            2: (4, 34),
            3: (3, 30),
        }
        root = Path(__file__).resolve().parent.parent
        for number, (topic_count, question_count) in expected.items():
            data = json.loads(
                (root / f"modulo{number}_fisica.json").read_text(encoding="utf-8")
            )
            result = import_physics_game(data, number, {})
            game = Disciplina.objects.get(slug=f"fisica-{number}")
            self.assertEqual(game.modulos.count(), topic_count)
            self.assertEqual(
                Fase.objects.filter(modulo__disciplina=game).count(),
                question_count,
            )
            self.assertEqual(
                Questao.objects.filter(fase__modulo__disciplina=game).count(),
                question_count,
            )
            self.assertEqual(result["questions"], question_count)
            for phase in Fase.objects.filter(modulo__disciplina=game):
                self.assertEqual(phase.questoes.count(), 1)

    def test_reimport_is_idempotent_for_structure_and_question_codes(self):
        import_physics_game(self.data, 3, {})
        import_physics_game(self.data, 3, {})

        game = Disciplina.objects.get(slug="fisica-3")
        self.assertEqual(game.modulos.count(), 3)
        self.assertEqual(Fase.objects.filter(modulo__disciplina=game).count(), 30)
        self.assertEqual(Questao.objects.filter(fase__modulo__disciplina=game).count(), 30)
        self.assertEqual(
            Questao.objects.filter(
                fase__modulo__disciplina=game,
                codigo_fonte__isnull=False,
            ).values("codigo_fonte").distinct().count(),
            30,
        )
