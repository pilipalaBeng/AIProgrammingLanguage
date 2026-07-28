import unittest
from pathlib import Path
from unittest.mock import patch

import lai_compiler
import lai_llvm_backend
from lai_ast import (
    AddExpr,
    FunctionDef,
    GroupExpr,
    IntExpr,
    LetStmt,
    MultiplyExpr,
    PrintStmt,
    Program,
    StringExpr,
    SubtractExpr,
    UnaryExpr,
)
from lai_compiler import compile_source, parse_source
from lai_core import LaiCompileError
from lai_llvm_backend import LLVM_BACKEND, build_llvm, generate_llvm


class LaiLlvmBackendTests(unittest.TestCase):
    def test_descriptor_uses_llvm_source_and_functions(self):
        self.assertEqual(LLVM_BACKEND.name, "llvm")
        self.assertEqual(LLVM_BACKEND.source_suffix, ".ll")
        self.assertIs(LLVM_BACKEND.build, build_llvm)

    def test_generates_textual_llvm_for_integer_print(self):
        llvm_ir = generate_llvm(parse_source("fn main() {\n    print(42)\n}"))

        self.assertIn(
            '@.fmt.int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"',
            llvm_ir,
        )
        self.assertIn("declare i32 @printf(ptr, ...)", llvm_ir)
        self.assertIn("define i32 @main() {", llvm_ir)
        self.assertIn(
            "%print0 = call i32 (ptr, ...) @printf(ptr @.fmt.int, i32 42)",
            llvm_ir,
        )
        self.assertTrue(llvm_ir.endswith("}\n"))

    def test_multiple_prints_use_unique_result_names(self):
        llvm_ir = generate_llvm(
            parse_source("fn main() {\n    print(42)\n    print(7)\n}")
        )

        self.assertIn("%print0 = call", llvm_ir)
        self.assertIn("%print1 = call", llvm_ir)

    def test_empty_main_returns_zero(self):
        llvm_ir = generate_llvm(parse_source("fn main() {\n}\n"))

        self.assertIn("entry:\n  ret i32 0", llvm_ir)

    def test_rejects_user_function(self):
        program = Program([], [FunctionDef("helper", [], 1)])
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: LLVM backend does not support FunctionDef yet",
        ):
            generate_llvm(program)

    def test_rejects_non_print_statement(self):
        program = Program([LetStmt("count", IntExpr(1), 2)])
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend does not support LetStmt yet",
        ):
            generate_llvm(program)

    def test_reports_earliest_llvm_capability_error_in_source_order(self):
        source = "fn main() {\n    print(true)\n    let count = 1\n}"

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend does not support BoolExpr yet",
        ):
            generate_llvm(parse_source(source))

    def test_rejects_malformed_arithmetic_chains_with_compile_error(self):
        cases = [
            (
                AddExpr([]),
                "line 1: LLVM backend AddExpr requires at least two operands",
            ),
            (
                AddExpr([IntExpr(1)]),
                "line 1: LLVM backend AddExpr requires at least two operands",
            ),
            (
                MultiplyExpr([]),
                "line 1: LLVM backend MultiplyExpr requires at least two operands",
            ),
            (
                MultiplyExpr([IntExpr(2)]),
                "line 1: LLVM backend MultiplyExpr requires at least two operands",
            ),
        ]

        for expression, error in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LaiCompileError, error):
                    generate_llvm(Program([PrintStmt(expression, 1)]))

    def test_rejects_integer_below_i32_literal_range(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: integer literal out of i32 range: -1",
        ):
            generate_llvm(Program([PrintStmt(IntExpr(-1), 1)]))

    def test_rejects_non_integer_print_expression(self):
        program = Program([PrintStmt(StringExpr("Hello"), 2)])
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend does not support StringExpr yet",
        ):
            generate_llvm(program)

    def test_v035_comparisons_preserve_capability_error(self):
        for operator in ("<", "<=", ">", ">=", "==", "!="):
            with self.subTest(operator=operator):
                program = parse_source(
                    f"fn main() {{\n    print(1 {operator} 2)\n}}"
                )
                with self.assertRaisesRegex(
                    LaiCompileError,
                    "line 2: LLVM backend does not support CompareExpr yet",
                ):
                    generate_llvm(program)

    def test_lowers_arithmetic_with_precedence_and_grouping(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n"
                "    print(2 + 3 * 4)\n"
                "    print((2 + 3) * 4)\n"
                "    print(9 - 4)\n"
                "}"
            )
        )

        expected_lines = [
            "  %value0 = mul i32 3, 4",
            "  %value1 = add i32 2, %value0",
            "  %print0 = call i32 (ptr, ...) @printf(ptr @.fmt.int, i32 %value1)",
            "  %value2 = add i32 2, 3",
            "  %value3 = mul i32 %value2, 4",
            "  %print1 = call i32 (ptr, ...) @printf(ptr @.fmt.int, i32 %value3)",
            "  %value4 = sub i32 9, 4",
            "  %print2 = call i32 (ptr, ...) @printf(ptr @.fmt.int, i32 %value4)",
        ]
        positions = [llvm_ir.index(line) for line in expected_lines]
        self.assertEqual(positions, sorted(positions))

    def test_arithmetic_prints_use_unique_value_names(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n"
                "    print(1 + 2 + 3)\n"
                "    print(2 * 3 * 4)\n"
                "}"
            )
        )

        self.assertEqual(llvm_ir.count("%value0 ="), 1)
        self.assertEqual(llvm_ir.count("%value1 ="), 1)
        self.assertEqual(llvm_ir.count("%value2 ="), 1)
        self.assertEqual(llvm_ir.count("%value3 ="), 1)
        self.assertNotIn("%value4 =", llvm_ir)

    def test_emits_unflagged_i32_wrapping_arithmetic(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n"
                "    print(2147483647 + 1)\n"
                "    print(0 - 2147483647 - 1)\n"
                "    print(65536 * 65536)\n"
                "}"
            )
        )

        self.assertIn("add i32 2147483647, 1", llvm_ir)
        self.assertIn("sub i32", llvm_ir)
        self.assertIn("mul i32 65536, 65536", llvm_ir)
        self.assertNotIn("nsw", llvm_ir)
        self.assertNotIn("nuw", llvm_ir)
        self.assertNotIn("exact", llvm_ir)

    def test_lowers_division_and_modulo(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n"
                "    print(8 / 2)\n"
                "    print(7 % 3)\n"
                "}"
            )
        )

        self.assertIn("  %value0 = sdiv i32 8, 2", llvm_ir)
        self.assertIn("  %value1 = srem i32 7, 3", llvm_ir)
        self.assertNotIn(" sdiv exact ", llvm_ir)

    def test_rejects_computed_division_by_zero(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2: division by zero"):
            generate_llvm(parse_source("fn main() {\n    print(8 / (1 - 1))\n}"))

    def test_rejects_computed_modulo_by_zero(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2: modulo by zero"):
            generate_llvm(parse_source("fn main() {\n    print(7 % (3 - 3))\n}"))

    def test_i32_wrap_is_used_when_checking_computed_zero_divisors(self):
        expressions = [
            "2147483647 + 1 + 2147483647 + 1",
            "0 - 2147483647 - 1 - 2147483647 - 1",
            "65536 * 65536",
        ]
        for expression in expressions:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(
                    LaiCompileError, "line 2: division by zero"
                ):
                    generate_llvm(
                        parse_source(
                            f"fn main() {{\n    print(1 / ({expression}))\n}}"
                        )
                    )

    def test_rejects_signed_division_overflow(self):
        source = (
            "fn main() {\n"
            "    print((0 - 2147483647 - 1) / (0 - 1))\n"
            "}"
        )
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend signed division overflow",
        ):
            generate_llvm(parse_source(source))

    def test_rejects_signed_remainder_overflow(self):
        source = (
            "fn main() {\n"
            "    print((0 - 2147483647 - 1) % (0 - 1))\n"
            "}"
        )
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend signed remainder overflow",
        ):
            generate_llvm(parse_source(source))

    def test_uses_truncating_signed_division_for_safety_evaluation(self):
        source = "fn main() {\n    print(1 / (((0 - 7) / 3) + 2))\n}"
        with self.assertRaisesRegex(LaiCompileError, "line 2: division by zero"):
            generate_llvm(parse_source(source))

    def test_uses_dividend_signed_remainder_for_safety_evaluation(self):
        source = "fn main() {\n    print(1 / (((0 - 7) % 3) + 1))\n}"
        with self.assertRaisesRegex(LaiCompileError, "line 2: division by zero"):
            generate_llvm(parse_source(source))

    def test_rejects_boolean_integer_literal_payload_inside_arithmetic(self):
        program = Program(
            [PrintStmt(AddExpr([IntExpr(1), IntExpr(True)]), 1)]
        )
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: integer literal must be int, got bool",
        ):
            generate_llvm(program)

    def test_rejects_float_integer_literal_payload_inside_arithmetic(self):
        program = Program(
            [PrintStmt(MultiplyExpr([IntExpr(2), IntExpr(1.0)]), 1)]
        )
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: integer literal must be int, got float",
        ):
            generate_llvm(program)

    def test_rejects_out_of_range_literal_inside_arithmetic(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: integer literal out of i32 range: 2147483648",
        ):
            generate_llvm(
                parse_source("fn main() {\n    print(1 + 2147483648)\n}")
            )

    def test_accepts_i32_upper_bound(self):
        llvm_ir = generate_llvm(
            parse_source("fn main() {\n    print(2147483647)\n}")
        )
        self.assertIn("i32 2147483647", llvm_ir)

    def test_lowers_unary_minus_and_elides_unary_plus(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n"
                "    print(-5)\n"
                "    print(+5)\n"
                "    print(2 * -3)\n"
                "    print(--5)\n"
                "}"
            )
        )

        self.assertIn("%value0 = sub i32 0, 5", llvm_ir)
        self.assertIn("@printf(ptr @.fmt.int, i32 5)", llvm_ir)
        self.assertIn("mul i32 2, %value", llvm_ir)
        self.assertEqual(llvm_ir.count("sub i32 0, 5"), 2)
        self.assertEqual(llvm_ir.count("sub i32 0,"), 4)
        self.assertNotIn("add i32 0, 5", llvm_ir)

    def test_lowers_i32_min_as_legal_constant(self):
        llvm_ir = generate_llvm(
            parse_source("fn main() {\n    print(-2147483648)\n}")
        )

        self.assertIn("@printf(ptr @.fmt.int, i32 -2147483648)", llvm_ir)
        self.assertNotIn("i32 2147483648", llvm_ir)

    def test_negative_division_and_modulo_keep_signed_semantics(self):
        llvm_ir = generate_llvm(
            parse_source(
                "fn main() {\n    print(-7 / 3)\n    print(-7 % 3)\n}"
            )
        )

        self.assertIn("sdiv i32", llvm_ir)
        self.assertIn("srem i32", llvm_ir)

    def test_direct_negative_i32_min_division_overflow_is_rejected(self):
        cases = [
            ("-2147483648 / -1", "signed division overflow"),
            ("-2147483648 % -1", "signed remainder overflow"),
        ]
        for expression, message in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LaiCompileError, message):
                    generate_llvm(
                        parse_source(f"fn main() {{\n    print({expression})\n}}")
                    )

    def test_rejects_unknown_unary_operator_ast(self):
        cases = [
            UnaryExpr("!", StringExpr("x")),
            UnaryExpr("!", IntExpr(2147483648)),
        ]
        for expression in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(
                    LaiCompileError,
                    "line 1: unsupported unary operator: !",
                ):
                    LLVM_BACKEND.emit(Program([PrintStmt(expression, 1)]))

    def test_rejects_boolean_integer_literal_payload(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: integer literal must be int, got bool",
        ):
            generate_llvm(Program([PrintStmt(IntExpr(True), 1)]))

    def test_rejects_float_integer_literal_payload(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: integer literal must be int, got float",
        ):
            generate_llvm(Program([PrintStmt(IntExpr(1.0), 1)]))

    def test_rejects_integer_above_i32_range(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: integer literal out of i32 range: 2147483648",
        ):
            generate_llvm(parse_source("fn main() {\n    print(2147483648)\n}"))

    def test_checked_entry_preserves_llvm_literal_validation(self):
        cases = [
            (IntExpr(True), "LLVM backend int literal must be int, got bool"),
            (IntExpr(1.0), "LLVM backend int literal must be int, got float"),
            (IntExpr(-1), "LLVM backend int literal out of i32 range: -1"),
            (IntExpr(2147483648), "LLVM backend int literal out of i32 range: 2147483648"),
        ]
        for expression, message in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LaiCompileError, message):
                    LLVM_BACKEND.emit(Program([PrintStmt(expression, 1)]))

    def test_direct_generator_runs_semantic_checker_first(self):
        program = parse_source("fn main() {\n    print(1 + missing)\n}")
        with self.assertRaisesRegex(LaiCompileError, "unknown variable: missing"):
            generate_llvm(program)

    def test_default_llvm_compile_source_checks_once_without_backend_recheck(self):
        source = "fn main() {\n    print(1 + 2)\n}"
        with patch(
            "lai_compiler.check_program", wraps=lai_compiler.check_program
        ) as compiler_checker, patch(
            "lai_llvm_backend.check_program", wraps=lai_llvm_backend.check_program
        ) as llvm_checker:
            llvm_ir = compile_source(source, LLVM_BACKEND)

        self.assertEqual(compiler_checker.call_count, 1)
        self.assertEqual(llvm_checker.call_count, 0)
        self.assertIn("add i32 1, 2", llvm_ir)

    def test_build_llvm_delegates_to_shared_clang_runner(self):
        with patch("lai_llvm_backend.build_with_clang") as build:
            build_llvm(Path("main.ll"), Path("main.exe"))
        build.assert_called_once_with(Path("main.ll"), Path("main.exe"))


if __name__ == "__main__":
    unittest.main()
