import json, unittest
from pathlib import Path
from curriculo.physics_engine import calculate, validate_scene_parameters
from curriculo.physics_module2_source import validate_source

class TestModule2Physics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((Path(__file__).resolve().parents[1]/'modulo2_fisica.json').read_text(encoding='utf-8'))
    def test_source_catalog(self):
        result=validate_source(self.data)
        self.assertEqual(result['phases'],4); self.assertEqual(result['exercises'],34)
        self.assertEqual(len(result['scenes']),34); self.assertEqual(len(result['formulas']),17)
    def test_numeric_defaults_match_reference_results(self):
        expected = {
            'fis2-ter-03': 77.0, 'fis2-ter-04': 42.0, 'fis2-ter-05': 360.0,
            'fis2-ter-06': 83.5, 'fis2-ter-07': 44.0, 'fis2-ter-08': 29.11392405063291,
            'fis2-td-04': 530.0, 'fis2-td-05': 40.0, 'fis2-td-06': 540.0,
            'fis2-td-07': 50.0, 'fis2-td-08': 1200.0, 'fis2-ond-03': 12.0,
            'fis2-ond-04': 8.0, 'fis2-opt-03': 1.8, 'fis2-opt-05': 22.5,
            'fis2-opt-06': 18.0, 'fis2-opt-07': -10.0,
        }
        for e in self.data['exercises']:
            a=e['challenge']['answer']
            if a['type']=='numeric':
                p={x['key']:x['value'] for x in e['simulation']['parameters']}
                value=calculate(a['formula'],p,self.data.get('constants'))
                self.assertAlmostEqual(value, expected[e['id']], places=7, msg=e['id'])
    def test_thermal_engine_domain(self):
        validate_scene_parameters('engine_efficiency',{'Qh':2500,'Qc':1500})
        with self.assertRaises(ValueError): validate_scene_parameters('engine_efficiency',{'Qh':1000,'Qc':1200})
    def test_pv_expansion_domain(self):
        validate_scene_parameters('pv_work',{'Vi':2,'Vf':5,'P':180})
        with self.assertRaises(ValueError): validate_scene_parameters('pv_work',{'Vi':5,'Vf':2,'P':180})
    def test_total_internal_reflection_is_physical(self):
        import math
        n1,n2,theta=1.5,1.1,math.radians(60)
        self.assertGreater(n1/n2*math.sin(theta),1)
if __name__=='__main__': unittest.main()
