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
from lai_int import is_i32_min_magnitude_expr, try_evaluate_static_int


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


if __name__ == "__main__":
    unittest.main()
