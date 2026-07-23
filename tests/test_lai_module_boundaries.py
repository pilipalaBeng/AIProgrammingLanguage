import unittest

import lai_backend
import lai_c_backend
import lai_checker
import lai_compiler
import lai_llvm_backend
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
