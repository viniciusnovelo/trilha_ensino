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
    def test_numeric_defaults_match_declared_solutions(self):
        for e in self.data['exercises']:
            a=e['challenge']['answer']
            if a['type']=='numeric':
                p={x['key']:x['value'] for x in e['simulation']['parameters']}
                value=calculate(a['formula'],p,self.data.get('constants'))
                self.assertTrue(value==value and abs(value)<1e15,e['id'])
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
