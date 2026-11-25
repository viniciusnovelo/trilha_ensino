"""Testes unitários independentes para as fórmulas do Matemática 3."""
import math
import unittest

from curriculo.math3_engine import calculate, is_correct, FORMULAS


class Math3EngineTests(unittest.TestCase):
    def test_formula_coverage(self):
        cases = {
            "distance_points": ({"x1": 1, "y1": 2, "x2": 4, "y2": 6}, 5),
            "midpoint": ({"x1": -2, "y1": 1, "x2": 4, "y2": 5}, {"x": 1, "y": 3}),
            "line_slope_points": ({"x1": 0, "y1": 1, "x2": 2, "y2": 5}, 2),
            "line_coefficients": ({"m": 2, "b": -3}, {"m": 2, "b": -3}),
            "line_relation": ({"m1": 2, "b1": 1, "m2": 2, "b2": -3}, "parallel"),
            "circle_r_squared": ({"r": 4}, 16),
            "circle_point_relation": ({"h": 1, "k": 1, "r": 3, "px": 4, "py": 1}, "on"),
            "larger_root": ({"r1": -2, "r2": 4}, 4),
            "smallest_root": ({"r1": -3, "r2": 1, "r3": 4}, -3),
            "inequality_integer_count": ({"r1": -2, "r2": 3}, 6),
            "girard_sum_product": ({"r1": 2, "r2": 5}, {"sum": 7, "product": 10}),
            "complex_product": ({"a": 2, "b": 1, "c": 1, "d": -1}, {"real": 3, "imag": -1}),
            "complex_positive_root": ({"k": 25}, 5),
            "relative_frequency_B": ({"fA": 4, "fB": 6, "fC": 10}, 30),
            "mean_five": ({"x1": 4, "x2": 6, "x3": 7, "x4": 9, "x5": 10}, 7.2),
            "population_variance_4": ({"x1": 2, "x2": 4, "x3": 6, "x4": 8}, 5),
            "population_std_4": ({"x1": 3, "x2": 5, "x3": 7, "x4": 9}, math.sqrt(5)),
            "conditional_percent": ({"joint": 12, "given": 20}, 60),
        }
        self.assertEqual(set(cases), FORMULAS)
        for formula, (params, expected) in cases.items():
            with self.subTest(formula=formula):
                actual = calculate(formula, params)
                if isinstance(expected, dict):
                    self.assertEqual(actual, expected)
                elif isinstance(expected, float):
                    self.assertAlmostEqual(actual, expected)
                else:
                    self.assertEqual(actual, expected)

    def test_line_relation_all_cases(self):
        self.assertEqual(calculate("line_relation", {"m1": 1, "b1": 2, "m2": 2, "b2": 2}), "secant")
        self.assertEqual(calculate("line_relation", {"m1": 1, "b1": 2, "m2": 1, "b2": 2}), "coincident")

    def test_integer_count_closed_interval_and_domain(self):
        self.assertEqual(calculate("inequality_integer_count", {"r1": -2.2, "r2": 3.2}), 6)
        self.assertEqual(calculate("inequality_integer_count", {"r1": -9, "r2": 9}), 11)
        self.assertEqual(calculate("inequality_integer_count", {"r1": 2.2, "r2": 2.8}), 0)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            calculate("unknown", {})
        with self.assertRaises(ValueError):
            calculate("distance_points", {"x1": float("nan"), "y1": 0, "x2": 1, "y2": 1})
        with self.assertRaises(ValueError):
            calculate("line_slope_points", {"x1": 2, "y1": 0, "x2": 2, "y2": 3})
        with self.assertRaises(ValueError):
            calculate("conditional_percent", {"joint": 12, "given": 0})

    def test_tolerance(self):
        self.assertTrue(is_correct("1.99", 2, 0.02))
        self.assertFalse(is_correct("1.97", 2, 0.02))
        self.assertFalse(is_correct("nan", 2, 0.02))


if __name__ == "__main__":
    unittest.main()
