"""Whitelist de fórmulas do Módulo 1 de Física. Nenhuma expressão é avaliada dinamicamente."""
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
SCENES = {
    'mru_track', 'incline_mru', 'mruv_track', 'free_fall', 'incline_mruv',
    'circular', 'inertia_bus', 'forces_balance', 'newton_cart',
    'compare_acceleration', 'rocket_action', 'skaters', 'work_wall_box',
    'work_horizontal', 'work_incline', 'kinetic_energy', 'potential_gravity',
    'spring', 'energy_hill', 'energy_two_heights', 'kepler_ellipse',
    'kepler_area', 'kepler_periods', 'satellite_orbit', 'gravity_field', 'gravity_energy',
}
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