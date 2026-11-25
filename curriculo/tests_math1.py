"""Testes estruturais e matemáticos do jogo Matemática 1."""
import json
from pathlib import Path
from django.test import TestCase
from .models import Disciplina, Fase, Questao
from .math1_import import import_math1_game
from .math1_engine import FORMULAS, calculate

class Math1GameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        root=Path(__file__).resolve().parent.parent
        cls.data=json.loads((root/"modulo1_matematica.json").read_text(encoding="utf-8"))

    def test_manifest_has_five_topics_and_35_exercises(self):
        self.assertEqual(len(self.data["phases"]),5)
        self.assertEqual(len(self.data["exercises"]),35)
        self.assertEqual(sum(x["exercise_count"] for x in self.data["phases"]),35)

    def test_every_numeric_formula_is_supported(self):
        formulas={x["challenge"]["answer"]["formula"] for x in self.data["exercises"] if x["challenge"]["answer"]["type"]=="numeric"}
        self.assertEqual(formulas,FORMULAS)

    def test_math1_imports_as_five_topics_and_35_single_question_phases(self):
        result=import_math1_game(self.data)
        game=Disciplina.objects.get(slug="matematica-1")
        self.assertEqual(game.modulos.count(),5)
        self.assertEqual(Fase.objects.filter(modulo__disciplina=game).count(),35)
        self.assertEqual(Questao.objects.filter(fase__modulo__disciplina=game).count(),35)
        for phase in Fase.objects.filter(modulo__disciplina=game):
            self.assertEqual(phase.questoes.count(),1)
        self.assertEqual(result["questions"],35)

    def test_reimport_is_idempotent(self):
        import_math1_game(self.data)
        import_math1_game(self.data)
        game=Disciplina.objects.get(slug="matematica-1")
        self.assertEqual(game.modulos.count(),5)
        self.assertEqual(Fase.objects.filter(modulo__disciplina=game).count(),35)
        self.assertEqual(Questao.objects.filter(fase__modulo__disciplina=game).count(),35)

    def test_key_calculations_and_constraints(self):
        self.assertEqual(calculate("rectangle_perimeter",{"width":8,"height":5}),26)
        self.assertAlmostEqual(calculate("ladder_height",{"ladder":10,"base":6}),8)
        self.assertEqual(calculate("frequency_count",{"value":3}),3)
        self.assertEqual(calculate("pa_term",{"first":4,"difference":3,"n":10}),31)
        self.assertAlmostEqual(calculate("pg_term",{"first":2,"ratio":3,"n":5}),162)
        with self.assertRaises(ValueError):
            calculate("ladder_height",{"ladder":6,"base":6})
