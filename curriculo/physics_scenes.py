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
SCENE_METADATA.update({
    'heat_concepts': {'label': 'heat concepts', 'kind': 'module2'},
    'latent_curve': {'label': 'latent curve', 'kind': 'module2'},
    'temperature_scales': {'label': 'temperature scales', 'kind': 'module2'},
    'sensible_heat': {'label': 'sensible heat', 'kind': 'module2'},
    'heat_capacity': {'label': 'heat capacity', 'kind': 'module2'},
    'latent_heat': {'label': 'latent heat', 'kind': 'module2'},
    'thermal_mixing': {'label': 'thermal mixing', 'kind': 'module2'},
    'thermal_mixing_capacity': {'label': 'thermal mixing capacity', 'kind': 'module2'},
    'zeroth_law': {'label': 'zeroth law', 'kind': 'module2'},
    'thermo_laws': {'label': 'thermo laws', 'kind': 'module2'},
    'pv_process': {'label': 'pv process', 'kind': 'module2'},
    'first_law': {'label': 'first law', 'kind': 'module2'},
    'engine_efficiency': {'label': 'engine efficiency', 'kind': 'module2'},
    'pv_work': {'label': 'pv work', 'kind': 'module2'},
    'carnot_efficiency': {'label': 'carnot efficiency', 'kind': 'module2'},
    'carnot_heat': {'label': 'carnot heat', 'kind': 'module2'},
    'wave_nature': {'label': 'wave nature', 'kind': 'module2'},
    'wave_direction': {'label': 'wave direction', 'kind': 'module2'},
    'wave_speed': {'label': 'wave speed', 'kind': 'module2'},
    'wave_frequency': {'label': 'wave frequency', 'kind': 'module2'},
    'wave_reflection': {'label': 'wave reflection', 'kind': 'module2'},
    'wave_refraction': {'label': 'wave refraction', 'kind': 'module2'},
    'wave_diffraction': {'label': 'wave diffraction', 'kind': 'module2'},
    'wave_interference': {'label': 'wave interference', 'kind': 'module2'},
    'wave_polarization': {'label': 'wave polarization', 'kind': 'module2'},
    'wave_resonance': {'label': 'wave resonance', 'kind': 'module2'},
    'light_reflection_refraction': {'label': 'light reflection refraction', 'kind': 'module2'},
    'light_absorption': {'label': 'light absorption', 'kind': 'module2'},
    'plane_mirror': {'label': 'plane mirror', 'kind': 'module2'},
    'convex_mirror': {'label': 'convex mirror', 'kind': 'module2'},
    'concave_mirror': {'label': 'concave mirror', 'kind': 'module2'},
    'converging_lens': {'label': 'converging lens', 'kind': 'module2'},
    'diverging_lens': {'label': 'diverging lens', 'kind': 'module2'},
    'human_eye': {'label': 'human eye', 'kind': 'module2'},
})

assert set(SCENE_METADATA) == SCENES


def validate_scene(scene: str) -> dict:
    if scene not in SCENE_METADATA:
        raise ValueError(f"cena não implementada: {scene}")
    return SCENE_METADATA[scene]