"""Motor de cálculos seguro da Química 2."""
import math

FORMULAS = {
    'compound_molar_mass', 'moles_from_mass', 'ammonia_from_nitrogen',
    'co2_mass', 'limiting_reagent', 'product_and_excess',
    'solution_status', 'kno3_solubility', 'common_concentration',
    'molar_concentration', 'required_solute_mass',
    'dilution_concentration', 'dbo_quality', 'water_problem_solution',
    'average_reaction_rate', 'temperature_effect', 'catalyst_effect',
    'surface_effect', 'relative_rate', 'corrosion_risk',
}

MOLAR_MASSES = {1: 18.0, 2: 44.0, 3: 58.5, 4: 100.1}
KNO3_CURVE = {20: 32, 30: 46, 40: 64, 50: 86, 60: 110, 70: 138, 80: 169}


def calculate(formula, params):
    if formula not in FORMULAS:
        raise ValueError('Fórmula não suportada.')

    def v(key):
        value = float(params[key])
        if not math.isfinite(value):
            raise ValueError('Parâmetro inválido.')
        return value

    if formula == 'compound_molar_mass':
        index = int(v('compoundIndex'))
        if index not in MOLAR_MASSES:
            raise ValueError('Composto inválido.')
        return MOLAR_MASSES[index]
    if formula == 'moles_from_mass':
        return v('mass') / v('molarMass')
    if formula == 'ammonia_from_nitrogen':
        return 2 * v('nN2')
    if formula == 'co2_mass':
        return v('massCaCO3') * 44.0 / 100.1
    if formula == 'limiting_reagent':
        h2, o2 = v('nH2') / 2, v('nO2')
        if math.isclose(h2, o2, rel_tol=0, abs_tol=1e-9):
            return 'none'
        return 'H2' if h2 < o2 else 'O2'
    if formula == 'product_and_excess':
        h2, o2 = v('nH2'), v('nO2')
        extent = min(h2 / 2, o2)
        water = 2 * extent
        excess = abs(o2 - extent) if h2 / 2 < o2 else abs(h2 - 2 * extent)
        return [water, excess]
    if formula == 'solution_status':
        solubility, mass = v('solubility'), v('soluteMass')
        if mass < solubility:
            return 'unsaturated'
        if math.isclose(mass, solubility, rel_tol=0, abs_tol=1e-9):
            return 'saturated'
        return 'excess'
    if formula == 'kno3_solubility':
        t = v('temperature')
        if t in KNO3_CURVE:
            return KNO3_CURVE[int(t)]
        lo = max(x for x in KNO3_CURVE if x < t)
        hi = min(x for x in KNO3_CURVE if x > t)
        return KNO3_CURVE[lo] + (KNO3_CURVE[hi] - KNO3_CURVE[lo]) * (t - lo) / (hi - lo)
    if formula == 'common_concentration':
        return v('mass') / v('volume')
    if formula == 'molar_concentration':
        return v('mass') / (v('molarMass') * v('volume'))
    if formula == 'required_solute_mass':
        return v('concentration') * v('volume')
    if formula == 'dilution_concentration':
        if v('V2') <= 0:
            raise ValueError('O volume final deve ser positivo.')
        return v('C1') * v('V1') / v('V2')
    if formula == 'dbo_quality':
        dbo = v('DBO')
        return 'low' if dbo < 3 else 'moderate' if dbo <= 5 else 'high'
    if formula == 'water_problem_solution':
        return {1: 'particles', 2: 'microbes', 3: 'dissolved'}[int(v('problemIndex'))]
    if formula == 'average_reaction_rate':
        return v('deltaC') / v('time')
    if formula == 'temperature_effect':
        t = v('temperature')
        return 'faster' if t > 25 else 'slower' if t < 25 else 'similar'
    if formula == 'catalyst_effect':
        return 'with' if v('catalyst') >= 0.5 else 'without'
    if formula == 'surface_effect':
        return {1: 'fast', 2: 'medium', 3: 'slow'}[int(v('surfaceIndex'))]
    if formula == 'relative_rate':
        score = (v('temperature') > 25) + (v('catalyst') >= 0.5) + (v('surfaceIndex') == 1)
        return 'high' if score >= 3 else 'medium' if score == 2 else 'low'
    if formula == 'corrosion_risk':
        return {1: 'low', 2: 'medium', 3: 'high'}[int(v('environmentIndex'))]
    raise ValueError('Fórmula não implementada.')


def is_correct(submitted, expected, tolerance=0):
    if isinstance(expected, str):
        return str(submitted) == expected
    if isinstance(expected, (list, tuple)):
        try:
            values = list(submitted)
            tol = float(tolerance)
            return len(values) == len(expected) and tol >= 0 and all(
                math.isfinite(float(a)) and abs(float(a) - float(b)) <= tol
                for a, b in zip(values, expected)
            )
        except (TypeError, ValueError):
            return False
    try:
        a, b, tol = float(submitted), float(expected), float(tolerance)
        return all(map(math.isfinite, (a, b, tol))) and tol >= 0 and abs(a - b) <= tol
    except (TypeError, ValueError):
        return False
