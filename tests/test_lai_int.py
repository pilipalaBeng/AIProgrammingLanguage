import unittest

from lai_ast import (
    AddExpr,
    DivideExpr,
    GroupExpr,
    IntExpr,
    ModuloExpr,
    MultiplyExpr,
    NameExpr,
    SubtractExpr,
    UnaryExpr,
)
from lai_int import (
    I32_MAX,
    StaticIntError,
    evaluate_static_i32,
    is_i32_min_magnitude_expr,
    try_evaluate_static_int,
)


class LaiIntTests(unittest.TestCase):
    def test_evaluates_literal_only_integer_tree(self):
        expr = UnaryExpr(
            "-",
            GroupExpr(AddExpr([IntExpr(2), MultiplyExpr([IntExpr(3), IntExpr(4)])])),
        )
        self.assertEqual(try_evaluate_static_int(expr), -14)

    def test_division_truncates_toward_zero(self):
        self.assertEqual(
            try_evaluate_static_int(DivideExpr(UnaryExpr("-", IntExpr(7)), IntExpr(3))),
            -2,
        )
        self.assertEqual(
            try_evaluate_static_int(ModuloExpr(UnaryExpr("-", IntExpr(7)), IntExpr(3))),
            -1,
        )

    def test_returns_none_for_dynamic_or_invalid_tree(self):
        self.assertIsNone(try_evaluate_static_int(NameExpr("step")))
        self.assertIsNone(try_evaluate_static_int(UnaryExpr("!", IntExpr(1))))
        self.assertIsNone(try_evaluate_static_int(DivideExpr(IntExpr(1), IntExpr(0))))

    def test_recognizes_only_grouped_i32_min_magnitude(self):
        self.assertTrue(is_i32_min_magnitude_expr(IntExpr(2147483648)))
        self.assertTrue(
            is_i32_min_magnitude_expr(GroupExpr(GroupExpr(IntExpr(2147483648))))
        )
        self.assertFalse(
            is_i32_min_magnitude_expr(UnaryExpr("+", IntExpr(2147483648)))
        )

    def test_evaluate_static_i32_returns_safe_values_or_dynamic(self):
        minimum = UnaryExpr("-", IntExpr(2147483648))
        self.assertEqual(evaluate_static_i32(AddExpr([IntExpr(1), IntExpr(2)])), 3)
        self.assertEqual(evaluate_static_i32(minimum), -2147483648)
        self.assertEqual(
            evaluate_static_i32(ModuloExpr(UnaryExpr("-", IntExpr(7)), IntExpr(3))),
            -1,
        )
        self.assertIsNone(
            evaluate_static_i32(AddExpr([NameExpr("value"), IntExpr(1)]))
        )

    def test_evaluate_static_i32_rejects_each_failure_kind(self):
        minimum = UnaryExpr("-", IntExpr(2147483648))
        cases = [
            (AddExpr([IntExpr(I32_MAX), IntExpr(1)]), "integer addition overflow"),
            (SubtractExpr(minimum, IntExpr(1)), "integer subtraction overflow"),
            (
                MultiplyExpr([IntExpr(1073741824), IntExpr(2)]),
                "integer multiplication overflow",
            ),
            (UnaryExpr("-", minimum), "integer unary negation overflow"),
            (DivideExpr(IntExpr(1), IntExpr(0)), "division by zero"),
            (ModuloExpr(IntExpr(1), IntExpr(0)), "modulo by zero"),
            (
                DivideExpr(minimum, UnaryExpr("-", IntExpr(1))),
                "integer division overflow",
            ),
            (
                ModuloExpr(minimum, UnaryExpr("-", IntExpr(1))),
                "integer modulo overflow",
            ),
            (
                AddExpr([IntExpr(I32_MAX), IntExpr(1), UnaryExpr("-", IntExpr(1))]),
                "integer addition overflow",
            ),
        ]
        for expression, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(StaticIntError, f"^{message}$"):
                    evaluate_static_i32(expression)


if __name__ == "__main__":
    unittest.main()
