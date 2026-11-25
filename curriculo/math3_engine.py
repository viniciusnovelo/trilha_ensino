"""Motor matemático seguro do Matemática 3. Sem eval e com fórmulas explícitas."""
import math

FORMULAS = {
    "distance_points", "midpoint", "line_slope_points", "line_coefficients",
    "line_relation", "circle_r_squared", "circle_point_relation",
    "larger_root", "smallest_root", "inequality_integer_count",
    "girard_sum_product", "complex_product", "complex_positive_root",
    "relative_frequency_B", "mean_five", "population_variance_4",
    "population_std_4", "conditional_percent",
}

def _values(params):
    result = {}
    for key, value in params.items():
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"Parâmetro inválido: {key}")
        result[key] = number
    return result

def calculate(formula, params):
    if formula not in FORMULAS:
        raise ValueError(f"Fórmula não suportada: {formula}")
    p = _values(params)
    def v(key):
        return p[key]
    if formula == "distance_points":
        result = math.hypot(v("x2") - v("x1"), v("y2") - v("y1"))
    elif formula == "midpoint":
        result = {"x": (v("x1") + v("x2")) / 2, "y": (v("y1") + v("y2")) / 2}
    elif formula == "line_slope_points":
        dx = v("x2") - v("x1")
        if dx == 0:
            raise ValueError("A reta é vertical; o coeficiente angular não está definido.")
        result = (v("y2") - v("y1")) / dx
    elif formula == "line_coefficients":
        result = {"m": v("m"), "b": v("b")}
    elif formula == "line_relation":
        if v("m1") != v("m2"):
            result = "secant"
        elif v("b1") == v("b2"):
            result = "coincident"
        else:
            result = "parallel"
    elif formula == "circle_r_squared":
        result = v("r") ** 2
    elif formula == "circle_point_relation":
        distance_squared = (v("px") - v("h")) ** 2 + (v("py") - v("k")) ** 2
        radius_squared = v("r") ** 2
        result = "on" if math.isclose(distance_squared, radius_squared, abs_tol=1e-9) else ("inside" if distance_squared < radius_squared else "outside")
    elif formula == "larger_root":
        result = max(v("r1"), v("r2"))
    elif formula == "smallest_root":
        result = min(v("r1"), v("r2"), v("r3"))
    elif formula == "inequality_integer_count":
        lo, hi = sorted((v("r1"), v("r2")))
        # A fonte define o intervalo fechado [r1, r2], limitado ao domínio [-5, 5].
        lower = max(-5, math.ceil(lo))
        upper = min(5, math.floor(hi))
        result = max(0, upper - lower + 1)
    elif formula == "girard_sum_product":
        result = {"sum": v("r1") + v("r2"), "product": v("r1") * v("r2")}
    elif formula == "complex_product":
        result = {"real": v("a") * v("c") - v("b") * v("d"), "imag": v("a") * v("d") + v("b") * v("c")}
    elif formula == "complex_positive_root":
        if v("k") < 0:
            raise ValueError("A constante deve ser não negativa.")
        result = math.sqrt(v("k"))
    elif formula == "relative_frequency_B":
        total = v("fA") + v("fB") + v("fC")
        if total <= 0:
            raise ValueError("A frequência total deve ser positiva.")
        result = 100 * v("fB") / total
    elif formula == "mean_five":
        result = sum(v(f"x{i}") for i in range(1, 6)) / 5
    elif formula == "population_variance_4":
        values = [v(f"x{i}") for i in range(1, 5)]
        mean = sum(values) / 4
        result = sum((x - mean) ** 2 for x in values) / 4
    elif formula == "population_std_4":
        values = [v(f"x{i}") for i in range(1, 5)]
        mean = sum(values) / 4
        result = math.sqrt(sum((x - mean) ** 2 for x in values) / 4)
    elif formula == "conditional_percent":
        if v("given") <= 0 or v("joint") < 0 or v("joint") > v("given"):
            raise ValueError("Frequências condicionais inválidas.")
        result = 100 * v("joint") / v("given")
    else:
        raise ValueError("Fórmula não implementada.")
    if isinstance(result, dict):
        if not all(math.isfinite(float(x)) for x in result.values()):
            raise ValueError("Resultado inválido.")
    elif isinstance(result, (int, float)) and not math.isfinite(result):
        raise ValueError("Resultado inválido.")
    return result

def is_correct(submitted, expected, tolerance):
    try:
        a, b, t = float(submitted), float(expected), float(tolerance)
        return all(map(math.isfinite, (a, b, t))) and t >= 0 and abs(a - b) <= t
    except (TypeError, ValueError):
        return False
