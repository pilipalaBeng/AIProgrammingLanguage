import unittest
from pathlib import Path
from unittest.mock import patch

import lai_compiler
import lai_llvm_backend
from lai_ast import AddExpr, FunctionDef, IntExpr, LetStmt, PrintStmt, Program, StringExpr
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

    def test_rejects_non_integer_print_expression(self):
        program = Program([PrintStmt(StringExpr("Hello"), 2)])
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend does not support StringExpr yet",
        ):
            generate_llvm(program)

    def test_rejects_arithmetic_print_expression(self):
        program = Program([PrintStmt(AddExpr([IntExpr(1), IntExpr(2)]), 2)])
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend does not support AddExpr yet",
        ):
            generate_llvm(program)

    def test_accepts_i32_upper_bound(self):
        llvm_ir = generate_llvm(
            parse_source("fn main() {\n    print(2147483647)\n}")
        )
        self.assertIn("i32 2147483647", llvm_ir)

    def test_rejects_integer_above_i32_range(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: LLVM backend int literal out of i32 range: 2147483648",
        ):
            generate_llvm(parse_source("fn main() {\n    print(2147483648)\n}"))

    def test_direct_generator_runs_semantic_checker_first(self):
        program = parse_source("fn main() {\n    print(missing)\n}")
        with self.assertRaisesRegex(LaiCompileError, "unknown variable: missing"):
            generate_llvm(program)

    def test_default_llvm_compile_source_checks_once_without_backend_recheck(self):
        source = "fn main() {\n    print(42)\n}"
        with patch(
            "lai_compiler.check_program", wraps=lai_compiler.check_program
        ) as compiler_checker, patch(
            "lai_llvm_backend.check_program", wraps=lai_llvm_backend.check_program
        ) as llvm_checker:
            llvm_ir = compile_source(source, LLVM_BACKEND)

        self.assertEqual(compiler_checker.call_count, 1)
        self.assertEqual(llvm_checker.call_count, 0)
        self.assertIn("i32 42", llvm_ir)

    def test_build_llvm_delegates_to_shared_clang_runner(self):
        with patch("lai_llvm_backend.build_with_clang") as build:
            build_llvm(Path("main.ll"), Path("main.exe"))
        build.assert_called_once_with(Path("main.ll"), Path("main.exe"))


if __name__ == "__main__":
    unittest.main()
