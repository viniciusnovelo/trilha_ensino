"""Motor seguro de fórmulas de Química 1."""
import math
FORMULAS={'water_phase','neutron_count','valence_electrons','element_from_z','period_from_z','covalent_order','oxygen_coefficient','water_from_oxygen','lavoisier_mass','water_oxygen_mass','fes_sulfur_mass','heat_quantity','energy_source_type'}
ELEMENTS=['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca']
def calculate(formula,p):
    if formula not in FORMULAS: raise ValueError('Fórmula não suportada.')
    def v(k):
        x=float(p[k])
        if not math.isfinite(x): raise ValueError('Parâmetro inválido.')
        return x
    if formula=='water_phase':
        t=v('temperature'); return 'transition' if t in (0,100) else ('solid' if t<0 else ('liquid' if t<100 else 'gas'))
    if formula=='neutron_count': return v('A')-v('Z')
    if formula=='valence_electrons':
        z=int(v('Z')); return z if z<=2 else z-2 if z<=10 else z-10 if z<=18 else z-18
    if formula=='element_from_z': return ELEMENTS[int(v('Z'))-1]
    if formula=='period_from_z':
        z=int(v('Z')); return '1' if z<=2 else '2' if z<=10 else '3' if z<=18 else '4'
    if formula=='covalent_order': return v('sharedPairs')
    if formula=='oxygen_coefficient': return 1
    if formula=='water_from_oxygen': return 2*v('o2')
    if formula=='lavoisier_mass': return v('massA')+v('massB')
    if formula=='water_oxygen_mass': return v('totalMass')*8/9
    if formula=='fes_sulfur_mass': return v('totalMass')*4/11
    if formula=='heat_quantity': return v('mass')*v('c')*v('deltaT')
    if formula=='energy_source_type': return 'renewable' if int(v('sourceIndex'))<=4 else 'nonrenewable'
    raise ValueError('Fórmula não implementada.')
def is_correct(submitted,expected,tolerance=0):
    if isinstance(expected,str): return str(submitted)==expected
    a,b,t=float(submitted),float(expected),float(tolerance)
    return all(map(math.isfinite,(a,b,t))) and t>=0 and abs(a-b)<=t
