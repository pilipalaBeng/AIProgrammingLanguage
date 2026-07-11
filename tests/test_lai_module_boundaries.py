import unittest

import lai_backend
import lai_c_backend
import lai_checker
import lai_compiler
from lai_core import LaiCompileError


class LaiModuleBoundaryTests(unittest.TestCase):
    def test_compiler_reexports_core_error_type(self):
        self.assertIs(lai_compiler.LaiCompileError, LaiCompileError)

    def test_compiler_reexports_checker_entry_point(self):
        self.assertIs(lai_compiler.check_program, lai_checker.check_program)

    def test_compiler_reexports_c_backend_entry_point(self):
        self.assertIs(lai_compiler.Backend, lai_backend.Backend)
        self.assertIs(lai_compiler.C_BACKEND, lai_c_backend.C_BACKEND)
        self.assertIs(lai_compiler.generate_c, lai_c_backend.generate_c)

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


if __name__ == "__main__":
    unittest.main()
