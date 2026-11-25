"""Testes do módulo Matemática 2."""
import json
from pathlib import Path
from django.test import TestCase
from .math2_engine import FORMULAS, calculate
from .math2_import import validate_math2_source, import_math2_game
from .models import Disciplina,Fase,Questao

class Math2Tests(TestCase):
 @classmethod
 def setUpTestData(cls):
  root=Path(__file__).resolve().parent.parent
  cls.data=json.loads((root/"modulo2_matematica.json").read_text(encoding="utf-8"))
 def test_manifest_and_formula_coverage(self):
  phases,grouped=validate_math2_source(self.data)
  self.assertEqual(len(phases),5)
  self.assertEqual(sum(map(len,grouped.values())),39)
  formulas={e["challenge"]["answer"]["formula"] for e in self.data["exercises"] if e["challenge"]["answer"]["type"]=="numeric"}
  self.assertEqual(formulas,FORMULAS)
 def test_import_structure_and_idempotence(self):
  import_math2_game(self.data); import_math2_game(self.data)
  game=Disciplina.objects.get(slug="matematica-2")
  self.assertEqual(game.modulos.count(),5)
  self.assertEqual(Fase.objects.filter(modulo__disciplina=game).count(),39)
  self.assertEqual(Questao.objects.filter(fase__modulo__disciplina=game).count(),39)
 def test_representative_formulas(self):
  self.assertEqual(calculate("euler_edges",{"vertices":8,"faces":6}),12)
  self.assertAlmostEqual(calculate("cylinder_volume",{"radius":3,"height":8}),72*3.141592653589793)
  self.assertEqual(calculate("determinant_2",{"a":2,"b":1,"c":3,"d":4}),5)
  self.assertEqual(calculate("combination",{"n":8,"k":3}),56)
  self.assertEqual(calculate("half_life_amount",{"initial":800,"half":5,"time":15}),100)
