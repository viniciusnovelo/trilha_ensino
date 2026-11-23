"""Registro das cenas aceitas pelo player do Módulo 1."""
from .physics_engine import SCENES

SCENE_METADATA = {
    'mru_track': {'label': 'Pista retilínea', 'kind': 'motion'},
    'incline_mru': {'label': 'Plano inclinado — MRU', 'kind': 'incline'},
    'mruv_track': {'label': 'Pista retilínea — MRUV', 'kind': 'motion'},
    'free_fall': {'label': 'Queda livre', 'kind': 'vertical'},
    'incline_mruv': {'label': 'Plano inclinado — MRUV', 'kind': 'incline'},
    'circular': {'label': 'Movimento circular', 'kind': 'orbit'},
    'inertia_bus': {'label': 'Ônibus e inércia', 'kind': 'vehicle'},
    'forces_balance': {'label': 'Balanço de forças', 'kind': 'forces'},
    'newton_cart': {'label': 'Carrinho — segunda lei', 'kind': 'forces'},
    'compare_acceleration': {'label': 'Comparação de acelerações', 'kind': 'comparison'},
    'rocket_action': {'label': 'Ação e reação no foguete', 'kind': 'rocket'},
    'skaters': {'label': 'Patinadores', 'kind': 'comparison'},
    'work_wall_box': {'label': 'Caixa contra a parede', 'kind': 'work'},
    'work_horizontal': {'label': 'Trabalho horizontal', 'kind': 'work'},
    'work_incline': {'label': 'Trabalho no plano inclinado', 'kind': 'incline'},
    'kinetic_energy': {'label': 'Energia cinética', 'kind': 'energy'},
    'potential_gravity': {'label': 'Energia potencial gravitacional', 'kind': 'energy'},
    'spring': {'label': 'Mola', 'kind': 'spring'},
    'energy_hill': {'label': 'Conservação de energia — rampa', 'kind': 'energy'},
    'energy_two_heights': {'label': 'Energia entre alturas', 'kind': 'energy'},
    'kepler_ellipse': {'label': 'Órbita elíptica', 'kind': 'orbit'},
    'kepler_area': {'label': 'Lei das áreas', 'kind': 'orbit'},
    'kepler_periods': {'label': 'Períodos orbitais', 'kind': 'orbit'},
    'satellite_orbit': {'label': 'Satélite em órbita', 'kind': 'orbit'},
    'gravity_field': {'label': 'Campo gravitacional', 'kind': 'field'},
    'gravity_energy': {'label': 'Energia gravitacional', 'kind': 'field'},
}
assert set(SCENE_METADATA) == SCENES


def validate_scene(scene: str) -> dict:
    if scene not in SCENE_METADATA:
        raise ValueError(f"cena não implementada: {scene}")
    return SCENE_METADATA[scene]