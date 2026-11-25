"""Motor matemático seguro do Matemática 1."""
import math

FORMULAS = {
    "real_operations", "ratio_proportion", "rule_three_direct", "rate_percent",
    "percent_part", "discounted_price", "simple_interest", "compound_amount",
    "pa_term", "algorithm_output", "linear_value", "linear_root",
    "quadratic_small_root", "vertex_x", "quadratic_max", "pg_term",
    "polygon_vertices", "rectangle_perimeter", "similar_side", "hypotenuse",
    "opposite_side", "opposite_tangent", "circle_area", "ladder_height",
    "graph_difference", "frequency_count", "arithmetic_mean",
}

def calculate(formula, p):
    if formula not in FORMULAS:
        raise ValueError(f"Fórmula matemática não suportada: {formula}")
    def v(key):
        x = float(p[key])
        if not math.isfinite(x):
            raise ValueError(f"Parâmetro inválido: {key}")
        return x
    if formula == "real_operations": result = v("A") - v("B") * v("C") + math.sqrt(v("N"))
    elif formula == "ratio_proportion": result = v("A") * v("C") / v("B")
    elif formula == "rule_three_direct": result = v("P1") * v("Q2") / v("Q1")
    elif formula == "rate_percent": result = v("part") / v("total") * 100
    elif formula == "percent_part": result = v("base") * v("rate") / 100
    elif formula == "discounted_price": result = v("price") * (1 - v("rate") / 100)
    elif formula == "simple_interest": result = v("capital") * v("rate") / 100 * v("periods")
    elif formula == "compound_amount": result = v("capital") * (1 + v("rate") / 100) ** v("periods")
    elif formula == "pa_term": result = v("first") + (v("n") - 1) * v("difference")
    elif formula == "algorithm_output": result = 2 * v("x") if v("x") > 10 else v("x") + 5
    elif formula == "linear_value": result = v("a") * v("x") + v("b")
    elif formula == "linear_root": result = -v("b") / v("a")
    elif formula == "quadratic_small_root":
        delta = v("b") ** 2 - 4 * v("a") * v("c")
        if delta < 0: raise ValueError("A função não possui raízes reais.")
        result = (-v("b") - math.sqrt(delta)) / (2 * v("a"))
    elif formula == "vertex_x": result = -v("b") / (2 * v("a"))
    elif formula == "quadratic_max":
        if v("a") >= 0: raise ValueError("A parábola não possui máximo.")
        xv = -v("b") / (2 * v("a"))
        result = v("a") * xv ** 2 + v("b") * xv + v("c")
    elif formula == "pg_term": result = v("first") * v("ratio") ** (v("n") - 1)
    elif formula == "polygon_vertices": result = v("sides")
    elif formula == "rectangle_perimeter": result = 2 * (v("width") + v("height"))
    elif formula == "similar_side": result = v("target") * v("corresponding") / v("small")
    elif formula == "hypotenuse": result = math.hypot(v("a"), v("b"))
    elif formula == "opposite_side": result = v("hyp") * math.sin(math.radians(v("angle")))
    elif formula == "opposite_tangent": result = v("adjacent") * math.tan(math.radians(v("angle")))
    elif formula == "circle_area": result = math.pi * v("radius") ** 2
    elif formula == "ladder_height":
        if v("ladder") <= v("base"): raise ValueError("O comprimento da escada deve ser maior que a distância horizontal.")
        result = math.sqrt(v("ladder") ** 2 - v("base") ** 2)
    elif formula == "graph_difference": result = v("end") - v("start")
    elif formula == "frequency_count": result = {1: 1, 2: 2, 3: 3, 4: 2, 5: 4}.get(int(v("value")), 0)
    elif formula == "arithmetic_mean": result = sum(v(k) for k in ("v1","v2","v3","v4","v5")) / 5
    else: raise ValueError("Fórmula não implementada.")
    if not math.isfinite(result): raise ValueError("O cálculo produziu resultado inválido.")
    return result

def is_correct(submitted, expected, tolerance):
    submitted, expected, tolerance = float(submitted), float(expected), float(tolerance)
    return all(map(math.isfinite, (submitted, expected, tolerance))) and tolerance >= 0 and abs(submitted - expected) <= tolerance
