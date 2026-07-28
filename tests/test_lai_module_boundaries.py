import unittest

import lai_ast
import lai_backend
import lai_c_backend
import lai_checker
import lai_compiler
import lai_llvm_backend
import lai_stdlib
from lai_core import LaiCompileError
from lai_ast import UnaryExpr


class LaiModuleBoundaryTests(unittest.TestCase):
    def test_compiler_reexports_core_error_type(self):
        self.assertIs(lai_compiler.LaiCompileError, LaiCompileError)

    def test_compiler_reexports_checker_entry_point(self):
        self.assertIs(lai_compiler.check_program, lai_checker.check_program)

    def test_compiler_reexports_c_backend_entry_point(self):
        self.assertIs(lai_compiler.Backend, lai_backend.Backend)
        self.assertIs(lai_compiler.C_BACKEND, lai_c_backend.C_BACKEND)
        self.assertIs(lai_compiler.generate_c, lai_c_backend.generate_c)
        self.assertIs(lai_compiler.LLVM_BACKEND, lai_llvm_backend.LLVM_BACKEND)

    def test_boolean_logic_ast_nodes_are_shared_across_module_boundaries(self):
        logical_not_type = getattr(lai_ast, "LogicalNotExpr", None)
        logical_type = getattr(lai_ast, "LogicalExpr", None)
        self.assertIsNotNone(logical_not_type)
        self.assertIsNotNone(logical_type)
        for module in (lai_compiler, lai_checker, lai_c_backend):
            with self.subTest(module=module.__name__):
                self.assertIs(getattr(module, "LogicalNotExpr", None), logical_not_type)
                self.assertIs(getattr(module, "LogicalExpr", None), logical_type)

    def test_c_backend_reuses_checker_logical_operator_set(self):
        self.assertIs(lai_c_backend.LOGICAL_OPERATORS, lai_checker.LOGICAL_OPERATORS)

    def test_c_backend_reuses_stdlib_runtime_support(self):
        self.assertIs(lai_c_backend.c_runtime_support, lai_stdlib.c_runtime_support)

    def test_split_checker_accepts_parser_ast(self):
        program = lai_compiler.parse_source("""fn main() {
    let count = 1 + 2
    let ready = count == 3
    if ready {
        print(count)
    }
}""")

        self.assertIsNone(lai_checker.check_program(program))

    def test_split_c_backend_generates_c_from_parser_ast(self):
        program = lai_compiler.parse_source("""fn main() {
    print("Hello")
}""")

        c_code = lai_c_backend.generate_c(program)

        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn('printf("Hello\\n");', c_code)

    def test_split_checker_and_c_backend_accept_unary_parser_ast(self):
        program = lai_compiler.parse_source("fn main() {\n    print(-5)\n}")

        self.assertIsInstance(program.statements[0].value, UnaryExpr)
        self.assertIsNone(lai_checker.check_program(program))
        self.assertIn('printf("%d\\n", (-(5)));', lai_c_backend.generate_c(program))


if __name__ == "__main__":
    unittest.main()
