import unittest

from lai_compiler import LaiCompileError, check_program, compile_source, parse_source
from lai_llvm_backend import LLVM_BACKEND


def program(body):
    return "fn main() {\n" + body + "\n}"


class LaiArrayTests(unittest.TestCase):
    def check(self, body):
        check_program(parse_source(program(body)))

    def test_three_element_types_and_empty_arrays(self):
        for kind, value in (("int", "1 + 2"), ("bool", "1 < 2"), ("string", '"LAI"')):
            for literal in (f"[{value}]", "[]"):
                with self.subTest(kind=kind, literal=literal):
                    self.check(f"let a: {kind}[] = {literal}")

    def test_reads_keep_element_types_in_existing_expressions(self):
        self.check('let a: int[] = [1, 2, 3]\n'
                   'let b: bool[] = [true]\n'
                   'let s: string[] = ["LAI"]\n'
                   'let result = -a[0] * a[1] + a[2]\n'
                   'result += a[0]\nresult -= a[0]\nresult *= a[1]\n'
                   'result /= a[0]\nresult %= a[1]\n'
                   'if b[0] and s[0] == "LAI" {\nprint(result)\n}\n'
                   'for i from a[0] to a[2] step a[1] {\nprint(a[i])\n}')

    def test_static_index_boundaries(self):
        for index in ("-1", "2", "1 + 1", "(3 * 2)", "-2147483648"):
            with self.subTest(index=index):
                with self.assertRaisesRegex(LaiCompileError, r"line 3: array index out of bounds: index -?\d+, length 2"):
                    self.check(f"let a: int[] = [10, 20]\nprint(a[{index}])")
        self.check("let a: int[] = [10, 20]\nprint(a[0])\nprint((a)[1])")

    def test_empty_array_has_no_valid_static_index(self):
        for kind in ("int", "string", "bool"):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(LaiCompileError, "index 0, length 0"):
                    self.check(f"let a: {kind}[] = []\nprint(a[0])")

    def test_index_requires_int_and_arithmetic_remains_checked(self):
        for index, error in (("true", "array index must be int, got bool"),
                             ('"0"', "array index must be int, got string"),
                             ("1 / 0", "division by zero"),
                             ("2147483647 + 1", "integer addition overflow")):
            with self.subTest(index=index):
                with self.assertRaisesRegex(LaiCompileError, error):
                    self.check(f"let a: int[] = [1]\nprint(a[{index}])")

    def test_rejects_mixed_elements(self):
        for kind, values, got in (("int", "1, true", "bool"),
                                  ("bool", "false, 1", "int"),
                                  ("string", '"a", 1', "int")):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(LaiCompileError, f"line 2: array element 2 must be {kind}, got {got}"):
                    self.check(f"let a: {kind}[] = [{values}]")

    def test_requires_explicit_array_declaration_and_literal(self):
        cases = [("let a = [1]", "array literals require an explicit local array declaration"),
                 ("let a = []", "array literals require an explicit local array declaration"),
                 ("let a: int[] = 1", "array declaration requires an array literal"),
                 ("let a: int = 1", "variable type annotation only supports"),
                 ("let a: float[] = []", "variable type annotation only supports"),
                 ("let a: int[][] = []", "variable type annotation only supports"),
                 ("let a: int[] = [[1]]", "array literals require an explicit local array declaration")]
        for body, error in cases:
            with self.subTest(body=body):
                with self.assertRaisesRegex(LaiCompileError, error):
                    self.check(body)

    def test_rejects_whole_array_operations(self):
        for statement in ("print(a)", "let b = a", "print(a == a)", "if a {\nprint(1)\n}"):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(LaiCompileError, "array a can only be used with an index"):
                    self.check(f"let a: int[] = [1]\n{statement}")
        with self.assertRaisesRegex(LaiCompileError, "whole-array assignment is not supported"):
            self.check("let a: int[] = [1]\na = [2]")
        with self.assertRaisesRegex(LaiCompileError, "array declaration requires an array literal"):
            self.check("let a: int[] = [1]\nlet b: int[] = a")

    def test_arrays_do_not_escape_through_functions(self):
        for source, error in (("fn f(a: int[]) {\n}\nfn main() {\n}", "array parameters are not supported"),
                              ("fn f() -> int[] {\nreturn 1\n}\nfn main() {\n}", "array return types are not supported"),
                              ("fn f(x: int) {\n}\nfn main() {\nlet a: int[] = [1]\nf(a)\n}", "array a can only be used with an index"),
                              ("fn f() -> int {\nlet a: int[] = [1]\nreturn a\n}\nfn main() {\n}", "array a can only be used with an index")):
            with self.subTest(error=error):
                with self.assertRaisesRegex(LaiCompileError, error):
                    check_program(parse_source(source))

    def test_scalar_elements_can_be_passed_and_returned(self):
        check_program(parse_source("fn f(x: int) -> int {\nlet a: int[] = [x]\nreturn a[0]\n}\n"
                                   "fn main() {\nlet a: int[] = [f(7)]\nprint(f(a[0]))\n}"))

    def test_scope_and_self_reference(self):
        for body, error in (("let a: int[] = [a[0]]", "unknown variable: a"),
                            ("if true {\nlet a: int[] = [1]\n}\nprint(a[0])", "unknown variable: a"),
                            ("let a = 1\nlet a: int[] = [1]", "variable already defined: a"),
                            ("for i from 0 to 1 {\nlet a: int[] = [i]\n}\nprint(a[0])", "unknown variable: a")):
            with self.subTest(body=body):
                with self.assertRaisesRegex(LaiCompileError, error):
                    self.check(body)
        self.check("if true {\nlet a: int[] = [1]\nprint(a[0])\n} else {\nlet a: int[] = [2, 3]\nprint(a[1])\n}")

    def test_index_target_must_be_a_local_array(self):
        for body in ("let a = 1\nprint(a[0])", 'print("a"[0])', "print([1][0])",
                     "let a: int[] = [1]\nprint(a[0][0])"):
            with self.subTest(body=body):
                with self.assertRaisesRegex(LaiCompileError, "index target must be a local array"):
                    self.check(body)

    def test_static_errors_are_checked_even_in_short_circuit(self):
        with self.assertRaisesRegex(LaiCompileError, "array index out of bounds"):
            self.check("let a: bool[] = []\nprint(false and a[0])")

    def test_llvm_rejects_valid_arrays_after_shared_checking(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2: LLVM backend does not support LetStmt yet"):
            compile_source(program("let a: int[] = [1]\nprint(a[0])"), backend=LLVM_BACKEND)
        with self.assertRaisesRegex(LaiCompileError, "array index out of bounds"):
            compile_source(program("let a: int[] = [1]\nprint(a[1])"), backend=LLVM_BACKEND)

    def test_existing_scalar_program_does_not_emit_array_runtime(self):
        self.assertNotIn("array_index", compile_source(program("print(1)")))


if __name__ == "__main__":
    unittest.main()
