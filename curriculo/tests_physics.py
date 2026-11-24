"""Testes unitários sem dependência de banco para engine e contrato das fontes."""
import json
import unittest
from pathlib import Path
from .physics_engine import calculate, FORMULAS, SCENES, is_correct
from .physics_scenes import validate_scene
from .physics_source import validate_source, validate_zip_archive


def source_path():
    candidates = [Path(__file__).resolve().parents[1] / 'modulo1_fisica.json',
                  Path(__file__).resolve().parents[1] / 'source' / 'modulo1_fisica.json',
                  Path('/mnt/data/modulo1_fisica.json')]
    return next((p for p in candidates if p.is_file()), None)


class PhysicsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = source_path()
        if path is None: raise unittest.SkipTest('modulo1_fisica.json não disponível para o teste')
        cls.data = json.loads(path.read_text(encoding='utf-8'))

    def test_all_numeric_formulas_are_whitelisted_and_calculable(self):
        numeric = [e for e in self.data['exercises'] if e['challenge']['answer']['type'] == 'numeric']
        self.assertEqual(len(numeric), 21)
        used = set()
        for exercise in numeric:
            answer = exercise['challenge']['answer']
            used.add(answer['formula'])
            params = {p['key']: p['value'] for p in exercise['simulation']['parameters']}
            value = calculate(answer['formula'], params, self.data.get('constants'))
            self.assertTrue(isinstance(value, float) and abs(value) < float('inf'))
        self.assertEqual(used, FORMULAS)

    def test_all_26_scenes_have_player_renderer_references(self):
        template = Path(__file__).resolve().parent / 'templates' / 'curriculo' / 'physics_player.html'
        source = template.read_text(encoding='utf-8')
        missing = sorted(scene for scene in SCENES if scene not in source)
        self.assertEqual(missing, [])

    def test_all_26_scenes_are_registered(self):
        used = {e['simulation']['scene'] for e in self.data['exercises']}
        self.assertEqual(len(used), 26)
        self.assertEqual(used, SCENES)
        for scene in used: self.assertTrue(validate_scene(scene)['label'])

    def test_full_source_validation(self):
        summary = validate_source(self.data)
        self.assertEqual(summary['exercises'], 28)
        self.assertEqual(len(summary['formulas']), 21)

    def test_zip_matches_main_json_exactly(self):
        candidates = [Path(__file__).resolve().parents[1] / 'exercicios.zip', Path(__file__).resolve().parents[1] / 'source' / 'exercicios.zip', Path('/mnt/data/exercicios.zip')]
        archive = next((p for p in candidates if p.is_file()), None)
        if archive is None: self.skipTest('exercicios.zip não disponível')
        result = validate_zip_archive(archive, self.data['exercises'])
        self.assertEqual(result, {'zip_files': 28, 'missing': 0, 'extra': 0, 'divergences': 0})

    def test_source_distribution(self):
        self.assertEqual(len(self.data['phases']), 4)
        self.assertEqual(len(self.data['exercises']), 28)
        types = [e['challenge']['answer']['type'] for e in self.data['exercises']]
        self.assertEqual(types.count('numeric'), 21)
        self.assertEqual(types.count('choice'), 7)

    def test_work_incline_uses_force_parallel_to_displacement(self):
        self.assertEqual(calculate('work_incline', {'F': 35, 'd': 4, 'theta': 25}), 140.0)

    def test_tolerance_is_absolute_and_inclusive(self):
        self.assertTrue(is_correct(10.02, 10, 0.02))
        self.assertFalse(is_correct(10.021, 10, 0.02))


    def test_player_submit_button_is_available_for_choice_and_numeric(self):
        template = Path(__file__).resolve().parent / 'templates' / 'curriculo' / 'physics_player.html'
        source = template.read_text(encoding='utf-8')
        self.assertIn('<div class="answer"><button class="btn" id="submit">Responder</button></div>', source)
        self.assertIn("if(q.type==='choice')", source)
        self.assertIn("$('numeric-answer').classList.remove('hidden')", source)


if __name__ == '__main__': unittest.main()