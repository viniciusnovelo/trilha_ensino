"""Whitelist de fórmulas dos Módulos 1, 2 e 3 de Física. Nenhuma expressão é avaliada dinamicamente."""
from __future__ import annotations
import math
from typing import Mapping

FORMULAS = {
    'mru_position', 'incline_height_mru', 'mruv_displacement', 'freefall_time',
    'incline_mruv_distance', 'centripetal_acceleration', 'net_force',
    'newton_acceleration', 'acceleration_difference', 'skater_a_acceleration',
    'work_constant', 'work_incline', 'kinetic_energy', 'gravitational_potential',
    'elastic_potential', 'energy_bottom_speed', 'energy_two_heights_speed',
    'gravity_force_kn', 'orbital_speed_kms', 'field_strength', 'gravity_potential_gj',
}
FORMULAS.update({
    'celsius_to_fahrenheit',
    'sensible_heat_kj',
    'thermal_capacity',
    'latent_heat_kj',
    'mix_temperature',
    'mix_temperature_capacity',
    'internal_energy_change',
    'heat_engine_efficiency_pct',
    'pv_work_j',
    'carnot_efficiency_pct',
    'carnot_rejected_heat',
    'wave_speed',
    'wave_frequency',
    'plane_mirror_distance',
    'concave_mirror_image',
    'converging_lens_image',
    'diverging_lens_image',
    'ohm_current', 'wire_resistance', 'series_resistance', 'parallel_resistance',
    'single_loop_vdrop_r2', 'single_loop_current', 'two_mesh_branch_voltage',
    'two_mesh_branch_current_r3', 'three_mesh_branch_current_r3', 'electric_power',
    'two_mesh_power_r3', 'magnetic_wire_uT', 'magnetic_loop_uT', 'magnetic_force_mN',
    'magnetic_flux_mWb', 'faraday_emf', 'electric_field_NC', 'electric_force_mN',
})
SCENES = {
    'mru_track', 'incline_mru', 'mruv_track', 'free_fall', 'incline_mruv',
    'circular', 'inertia_bus', 'forces_balance', 'newton_cart',
    'compare_acceleration', 'rocket_action', 'skaters', 'work_wall_box',
    'work_horizontal', 'work_incline', 'kinetic_energy', 'potential_gravity',
    'spring', 'energy_hill', 'energy_two_heights', 'kepler_ellipse',
    'kepler_area', 'kepler_periods', 'satellite_orbit', 'gravity_field', 'gravity_energy',
}
SCENES.update({
    'heat_concepts',
    'latent_curve',
    'temperature_scales',
    'sensible_heat',
    'heat_capacity',
    'latent_heat',
    'thermal_mixing',
    'thermal_mixing_capacity',
    'zeroth_law',
    'thermo_laws',
    'pv_process',
    'first_law',
    'engine_efficiency',
    'pv_work',
    'carnot_efficiency',
    'carnot_heat',
    'wave_nature',
    'wave_direction',
    'wave_speed',
    'wave_frequency',
    'wave_reflection',
    'wave_refraction',
    'wave_diffraction',
    'wave_interference',
    'wave_polarization',
    'wave_resonance',
    'light_reflection_refraction',
    'light_absorption',
    'plane_mirror',
    'convex_mirror',
    'concave_mirror',
    'converging_lens',
    'diverging_lens',
    'human_eye',
    'circuit_concepts', 'electric_field', 'electric_field_calc', 'electric_force',
    'electric_power', 'faraday_concept', 'faraday_law', 'general_relativity',
    'induction_motor', 'ionizing_radiation', 'lenz_law', 'magnetic_field',
    'magnetic_flux', 'magnetic_force', 'magnetic_loop', 'magnetic_wire', 'ohm_law',
    'ohm_second_law', 'parallel_circuit', 'quantum_levels', 'radiation_penetration',
    'series_circuit', 'single_loop_current', 'single_loop_drop', 'special_relativity',
    'three_mesh_circuit', 'two_mesh_circuit', 'two_mesh_power', 'wave_particle',
})
CONSTANTS = {'G': 6.67e-11, 'earth_mass': 5.97e24, 'earth_radius': 6_370_000.0, 'pi': math.pi}


def _p(parameters: Mapping[str, float], key: str) -> float:
    if key not in parameters:
        raise ValueError(f"parâmetro obrigatório ausente: {key}")
    value = float(parameters[key])
    if not math.isfinite(value):
        raise ValueError(f"parâmetro inválido: {key}")
    return value


def calculate(formula: str, parameters: Mapping[str, float], constants=None) -> float:
    """Resolve exclusivamente identificadores declarados na whitelist."""
    if formula not in FORMULAS:
        raise ValueError(f"fórmula não suportada: {formula}")
    c = {**CONSTANTS, **(constants or {})}
    pi = float(c['pi'])
    if formula == 'mru_position': result = _p(parameters, 'x0') + _p(parameters, 'v') * _p(parameters, 't')
    elif formula == 'incline_height_mru': result = _p(parameters, 'v') * _p(parameters, 't') * math.sin(math.radians(_p(parameters, 'theta')))
    elif formula == 'mruv_displacement': result = _p(parameters, 'v0') * _p(parameters, 't') + 0.5 * _p(parameters, 'a') * _p(parameters, 't') ** 2
    elif formula == 'freefall_time': result = math.sqrt(2 * _p(parameters, 'h') / _p(parameters, 'g'))
    elif formula == 'incline_mruv_distance': result = 0.5 * _p(parameters, 'g') * math.sin(math.radians(_p(parameters, 'theta'))) * _p(parameters, 't') ** 2
    elif formula == 'centripetal_acceleration': result = 4 * pi ** 2 * _p(parameters, 'r') / _p(parameters, 'T') ** 2
    elif formula == 'net_force': result = _p(parameters, 'right') - _p(parameters, 'left')
    elif formula == 'newton_acceleration': result = _p(parameters, 'F') / _p(parameters, 'm')
    elif formula == 'acceleration_difference': result = _p(parameters, 'F') / _p(parameters, 'm1') - _p(parameters, 'F') / _p(parameters, 'm2')
    elif formula == 'skater_a_acceleration': result = _p(parameters, 'F') / _p(parameters, 'm1')
    elif formula == 'work_constant': result = _p(parameters, 'F') * _p(parameters, 'd') * math.cos(math.radians(_p(parameters, 'alpha')))
    elif formula == 'work_incline': result = _p(parameters, 'F') * _p(parameters, 'd')
    elif formula == 'kinetic_energy': result = 0.5 * _p(parameters, 'm') * _p(parameters, 'v') ** 2
    elif formula == 'gravitational_potential': result = _p(parameters, 'm') * _p(parameters, 'g') * _p(parameters, 'h')
    elif formula == 'elastic_potential': result = 0.5 * _p(parameters, 'k') * _p(parameters, 'x') ** 2
    elif formula == 'energy_bottom_speed': result = math.sqrt(2 * _p(parameters, 'g') * _p(parameters, 'h'))
    elif formula == 'energy_two_heights_speed': result = math.sqrt(max(0.0, _p(parameters, 'vi') ** 2 + 2 * _p(parameters, 'g') * (_p(parameters, 'hi') - _p(parameters, 'hf'))))
    elif formula == 'gravity_force_kn': result = (float(c['G']) * float(c['earth_mass']) * _p(parameters, 'm') / _p(parameters, 'r') ** 2) / 1000
    elif formula == 'orbital_speed_kms': result = math.sqrt(float(c['G']) * float(c['earth_mass']) / (float(c['earth_radius']) + _p(parameters, 'alt'))) / 1000
    elif formula == 'field_strength': result = float(c['G']) * float(c['earth_mass']) / (float(c['earth_radius']) + _p(parameters, 'alt')) ** 2
    elif formula == 'gravity_potential_gj': result = (-float(c['G']) * float(c['earth_mass']) * _p(parameters, 'm') / _p(parameters, 'r')) / 1e9
    elif formula == 'celsius_to_fahrenheit': result = _p(parameters, 'tempC') * 9 / 5 + 32
    elif formula == 'sensible_heat_kj': result = _p(parameters, 'm') * _p(parameters, 'c') * _p(parameters, 'dT') / 1000
    elif formula == 'thermal_capacity': result = _p(parameters, 'm') * _p(parameters, 'c')
    elif formula == 'latent_heat_kj': result = _p(parameters, 'm') * _p(parameters, 'L')
    elif formula == 'mix_temperature': result = (_p(parameters, 'm1') * _p(parameters, 'T1') + _p(parameters, 'm2') * _p(parameters, 'T2')) / (_p(parameters, 'm1') + _p(parameters, 'm2'))
    elif formula == 'mix_temperature_capacity': result = (_p(parameters, 'm1') * _p(parameters, 'c1') * _p(parameters, 'T1') + _p(parameters, 'm2') * _p(parameters, 'c2') * _p(parameters, 'T2')) / (_p(parameters, 'm1') * _p(parameters, 'c1') + _p(parameters, 'm2') * _p(parameters, 'c2'))
    elif formula == 'internal_energy_change': result = _p(parameters, 'Q') - _p(parameters, 'W')
    elif formula == 'heat_engine_efficiency_pct': result = (_p(parameters, 'Qh') - _p(parameters, 'Qc')) / _p(parameters, 'Qh') * 100
    elif formula == 'pv_work_j': result = _p(parameters, 'P') * (_p(parameters, 'Vf') - _p(parameters, 'Vi'))
    elif formula == 'carnot_efficiency_pct': result = (1 - _p(parameters, 'Tc') / _p(parameters, 'Th')) * 100
    elif formula == 'carnot_rejected_heat': result = _p(parameters, 'Qh') * _p(parameters, 'Tc') / _p(parameters, 'Th')
    elif formula == 'wave_speed': result = _p(parameters, 'lambda') * _p(parameters, 'f')
    elif formula == 'wave_frequency': result = _p(parameters, 'v') / _p(parameters, 'lambda')
    elif formula == 'plane_mirror_distance': result = _p(parameters, 'p')
    elif formula in {'concave_mirror_image', 'converging_lens_image', 'diverging_lens_image'}:
        focal, obj = _p(parameters, 'f'), _p(parameters, 'p')
        if abs(obj - focal) < 1e-12:
            raise ValueError('objeto no foco: imagem no infinito')
        result = focal * obj / (obj - focal)
    elif formula == 'ohm_current': result = _p(parameters, 'V') / _p(parameters, 'R')
    elif formula == 'wire_resistance': result = _p(parameters, 'rho') * _p(parameters, 'L') / (_p(parameters, 'A') * 1e-6)
    elif formula == 'series_resistance': result = _p(parameters, 'R1') + _p(parameters, 'R2') + _p(parameters, 'R3')
    elif formula == 'parallel_resistance': result = 1 / (1 / _p(parameters, 'R1') + 1 / _p(parameters, 'R2'))
    elif formula == 'single_loop_vdrop_r2':
        current = _p(parameters, 'V') / (_p(parameters, 'R1') + _p(parameters, 'R2'))
        result = current * _p(parameters, 'R2')
    elif formula == 'single_loop_current': result = _p(parameters, 'V') / (_p(parameters, 'R1') + _p(parameters, 'R2') + _p(parameters, 'R3'))
    elif formula == 'two_mesh_branch_voltage':
        equivalent = _p(parameters, 'R1') + (_p(parameters, 'R2') * _p(parameters, 'R3')) / (_p(parameters, 'R2') + _p(parameters, 'R3'))
        result = _p(parameters, 'V') * ((_p(parameters, 'R2') * _p(parameters, 'R3')) / (_p(parameters, 'R2') + _p(parameters, 'R3'))) / equivalent
    elif formula == 'two_mesh_branch_current_r3':
        branch_voltage = calculate('two_mesh_branch_voltage', parameters, constants)
        result = branch_voltage / _p(parameters, 'R3')
    elif formula == 'three_mesh_branch_current_r3':
        parallel = 1 / (1 / _p(parameters, 'R2') + 1 / _p(parameters, 'R3') + 1 / _p(parameters, 'R4'))
        total_current = _p(parameters, 'V') / (_p(parameters, 'R1') + parallel)
        branch_voltage = total_current * parallel
        result = branch_voltage / _p(parameters, 'R3')
    elif formula == 'electric_power': result = _p(parameters, 'V') ** 2 / _p(parameters, 'R')
    elif formula == 'two_mesh_power_r3':
        current = calculate('two_mesh_branch_current_r3', parameters, constants)
        result = current ** 2 * _p(parameters, 'R3')
    elif formula == 'magnetic_wire_uT': result = (float(c['vacuum_permeability']) * _p(parameters, 'I') / (2 * pi * _p(parameters, 'r'))) * 1e6
    elif formula == 'magnetic_loop_uT': result = (float(c['vacuum_permeability']) * _p(parameters, 'I') / (2 * _p(parameters, 'R'))) * 1e6
    elif formula == 'magnetic_force_mN': result = abs(_p(parameters, 'q')) * 1e-6 * _p(parameters, 'v') * _p(parameters, 'B') * abs(math.sin(math.radians(_p(parameters, 'theta')))) * 1000
    elif formula == 'magnetic_flux_mWb': result = _p(parameters, 'B') * _p(parameters, 'A') * math.cos(math.radians(_p(parameters, 'theta'))) * 1000
    elif formula == 'faraday_emf': result = _p(parameters, 'N') * abs(_p(parameters, 'dPhi')) / _p(parameters, 'dt')
    elif formula == 'electric_field_NC': result = _p(parameters, 'F') / (_p(parameters, 'q') * 1e-6)
    elif formula == 'electric_force_mN': result = abs(_p(parameters, 'q')) * 1e-6 * _p(parameters, 'E') * 1000
    else:  # pragma: no cover - proteção redundante
        raise ValueError(f"fórmula não suportada: {formula}")
    if not math.isfinite(result):
        raise ValueError(f"resultado não finito para a fórmula: {formula}")
    return result


def is_correct(submitted: float, expected: float, tolerance: float) -> bool:
    """A tolerância absoluta é a que está declarada no JSON de cada exercício."""
    submitted, expected, tolerance = float(submitted), float(expected), float(tolerance)
    if tolerance < 0 or not all(map(math.isfinite, (submitted, expected, tolerance))):
        raise ValueError('resposta ou tolerância inválida')
    return abs(submitted - expected) <= tolerance

def validate_scene_parameters(scene: str, parameters: Mapping[str, float]) -> None:
    """Valida relações físicas entre controles que não podem ser verificadas isoladamente."""
    p = parameters
    if scene == 'engine_efficiency' and not (0 < _p(p, 'Qc') < _p(p, 'Qh')):
        raise ValueError('o calor rejeitado deve ser positivo e menor que o calor recebido')
    if scene == 'thermo_laws' and not (0 <= _p(p, 'W') <= _p(p, 'Qh')):
        raise ValueError('o trabalho não pode exceder o calor recebido neste esquema')
    if scene == 'pv_work_j' or scene == 'pv_work':
        if not _p(p, 'Vf') > _p(p, 'Vi'):
            raise ValueError('a transformação representada é uma expansão: Vf deve ser maior que Vi')
    if scene in {'carnot_efficiency', 'carnot_heat'} and not (0 < _p(p, 'Tc') < _p(p, 'Th')):
        raise ValueError('a fonte fria deve estar abaixo da fonte quente em kelvin')
    if scene == 'light_reflection_refraction' and (_p(p, 'n1') <= 0 or _p(p, 'n2') <= 0):
        raise ValueError('índices de refração devem ser positivos')
