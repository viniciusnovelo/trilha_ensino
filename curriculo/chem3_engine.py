"""Motor de cálculos seguro da Química 3."""
import math

FORMULAS = {
    'carbon_valence', 'chain_classification', 'chain_topology', 'bond_order',
    'hybrid_geometry', 'representation_meaning', 'hydrocarbon_name',
    'alcohol_or_ether', 'aldehyde_or_ketone', 'acid_or_ester', 'amine_or_amide',
    'functional_group', 'daily_function', 'planar_isomerism', 'cis_trans',
    'chiral_carbon', 'reaction_type', 'polymer_origin', 'polymerization_type',
    'plastic_application', 'carbohydrate_class', 'lipid_function',
    'protein_structure', 'equilibrium_status', 'kc_ammonia',
    'le_chatelier_shift', 'ph_class', 'ph_from_oh_exponent',
}


def calculate(formula, params):
    if formula not in FORMULAS:
        raise ValueError('Fórmula não suportada.')

    def v(key):
        value = float(params[key])
        if not math.isfinite(value):
            raise ValueError('Parâmetro inválido.')
        return value

    def index(key, low, high):
        value = v(key)
        if not value.is_integer() or not low <= int(value) <= high:
            raise ValueError('Índice de parâmetro inválido.')
        return int(value)

    if formula == 'carbon_valence':
        n = index('bondUnits', 1, 5)
        return 'complete' if n == 4 else 'incomplete' if n < 4 else 'exceeded'
    if formula == 'chain_classification':
        return ['open_normal_saturated', 'open_branched_unsaturated', 'closed_saturated', 'open_heterogeneous'][index('chainType', 1, 4)-1]
    if formula == 'chain_topology':
        return ['open_normal', 'open_branched', 'closed_normal', 'closed_branched'][index('topology', 1, 4)-1]
    if formula == 'bond_order':
        return ['single', 'double', 'triple'][index('bondOrder', 1, 3)-1]
    if formula == 'hybrid_geometry':
        return ['tetrahedral', 'trigonal_planar', 'linear'][index('hybridIndex', 1, 3)-1]
    if formula == 'representation_meaning':
        return ['molecular', 'condensed', 'skeletal'][index('representationIndex', 1, 3)-1]
    if formula == 'hydrocarbon_name':
        return ['etano', 'eteno', 'etino', 'propano', 'propeno', 'butano'][index('compoundIndex', 1, 6)-1]
    if formula == 'alcohol_or_ether':
        return 'alcohol' if index('moleculeIndex', 1, 2) == 1 else 'ether'
    if formula == 'aldehyde_or_ketone':
        return 'aldehyde' if index('moleculeIndex', 1, 2) == 1 else 'ketone'
    if formula == 'acid_or_ester':
        return 'carboxylic_acid' if index('moleculeIndex', 1, 2) == 1 else 'ester'
    if formula == 'amine_or_amide':
        return 'amine' if index('moleculeIndex', 1, 2) == 1 else 'amide'
    if formula == 'functional_group':
        return ['hydrocarbon', 'alcohol', 'ether', 'aldehyde', 'ketone', 'acid', 'ester', 'amine', 'amide'][index('groupIndex', 1, 9)-1]
    if formula == 'daily_function':
        return ['alcohol', 'ketone', 'acid', 'ester', 'amine'][index('substanceIndex', 1, 5)-1]
    if formula == 'planar_isomerism':
        return ['chain', 'position', 'function'][index('isomerIndex', 1, 3)-1]
    if formula == 'cis_trans':
        return 'cis' if index('geometryIndex', 1, 2) == 1 else 'trans'
    if formula == 'chiral_carbon':
        return 'yes' if index('substituentSet', 1, 2) == 1 else 'no'
    if formula == 'reaction_type':
        return ['substitution', 'addition', 'elimination'][index('reactionIndex', 1, 3)-1]
    if formula == 'polymer_origin':
        return 'natural' if index('polymerIndex', 1, 6) <= 3 else 'synthetic'
    if formula == 'polymerization_type':
        return 'addition' if index('monomerIndex', 1, 3) == 1 else 'condensation'
    if formula == 'plastic_application':
        return ['flexible_packaging', 'bottles_fibers', 'pipes_profiles', 'containers_housewares'][index('plasticIndex', 1, 4)-1]
    if formula == 'carbohydrate_class':
        return ['mono', 'di', 'poly'][index('carbohydrateIndex', 1, 3)-1]
    if formula == 'lipid_function':
        return ['energy_storage', 'membrane', 'waterproofing'][index('lipidIndex', 1, 3)-1]
    if formula == 'protein_structure':
        return ['primary', 'secondary', 'tertiary', 'quaternary'][index('proteinLevel', 1, 4)-1]
    if formula == 'equilibrium_status':
        direct, reverse = v('forwardRate'), v('reverseRate')
        return 'equilibrium' if math.isclose(direct, reverse, abs_tol=1e-9) else 'forward' if direct > reverse else 'reverse'
    if formula == 'kc_ammonia':
        n2, h2 = v('n2'), v('h2')
        if n2 <= 0 or h2 <= 0:
            raise ValueError('As concentrações de N₂ e H₂ devem ser positivas.')
        return (v('nh3') ** 2) / (n2 * (h2 ** 3))
    if formula == 'le_chatelier_shift':
        return ['right', 'right', 'right', 'left', 'right', 'no_shift'][index('scenarioIndex', 1, 6)-1]
    if formula == 'ph_class':
        ph = v('phValue')
        return 'acidic' if ph < 7 else 'neutral' if math.isclose(ph, 7, abs_tol=1e-9) else 'basic'
    if formula == 'ph_from_oh_exponent':
        exponent = v('ohExponent')
        if not 0 <= exponent <= 14:
            raise ValueError('Expoente de pOH fora da faixa química esperada.')
        return 14 - exponent
    raise ValueError('Fórmula não implementada.')


def is_correct(submitted, expected, tolerance=0):
    if isinstance(expected, str):
        return str(submitted) == expected
    try:
        a, b, tol = float(submitted), float(expected), float(tolerance)
        return all(map(math.isfinite, (a, b, tol))) and tol >= 0 and abs(a - b) <= tol
    except (TypeError, ValueError):
        return False
