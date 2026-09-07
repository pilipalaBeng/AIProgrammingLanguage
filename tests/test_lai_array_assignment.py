import unittest
from dataclasses import FrozenInstanceError, fields

import lai_ast
import lai_compiler
from lai_compiler import LaiCompileError, check_program, compile_source, parse_source
from lai_llvm_backend import LLVM_BACKEND


def program(body):
    return "fn main() {\n" + body + "\n}"


class LaiArrayAssignmentTests(unittest.TestCase):
    def check(self, body):
        check_program(parse_source(program(body)))

    def test_node_and_compatibility_export(self):
        node = getattr(lai_ast, "IndexAssignStmt", None)
        self.assertIsNotNone(node)
        self.assertIs(getattr(lai_compiler, "IndexAssignStmt", None), node)
        self.assertEqual([f.name for f in fields(node)], ["target", "operator", "value", "line"])
        statement = parse_source(program("a[0] = 1")).statements[0]
        self.assertIsInstance(statement, node)
        self.assertEqual(statement.operator, "=")
        with self.assertRaises(FrozenInstanceError):
            statement.line = 4

    def test_plain_assignment_for_all_types(self):
        for kind, value in (("int", "1 + 2"), ("string", '"LAI"'), ("bool", "true or false")):
            with self.subTest(kind=kind):
                self.check(f"let a: {kind}[] = [{value}]\na[0] = {value}\nprint(a[0])")

    def test_all_integer_compounds_and_grouped_target(self):
        for operator in ("+=", "-=", "*=", "/=", "%="):
            with self.subTest(operator=operator):
                self.check(f"let a: int[] = [10, 2]\n(a)[a[1] - 2] {operator} a[1]")

    def test_assignment_preserves_array_type_and_length(self):
        for operator in ("=", "+=", "-=", "*=", "/=", "%="):
            with self.subTest(operator=operator):
                with self.assertRaisesRegex(LaiCompileError, "line 4: array index out of bounds: index 1, length 1"):
                    self.check(f"let a: int[] = [1]\na[0] {operator} 2\nprint(a[1])")

    def test_assignment_type_must_match(self):
        for kind, initial, value, got in (("int", "1", "true", "bool"),
                                         ("bool", "true", "1", "int"),
                                         ("string", '"a"', "1", "int")):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(LaiCompileError, f"line 3: cannot assign {got} to array element of type {kind}"):
                    self.check(f"let a: {kind}[] = [{initial}]\na[0] = {value}")

    def test_compounds_require_integer_element_and_rhs(self):
        for operator in ("+=", "-=", "*=", "/=", "%="):
            for kind, initial in (("bool", "true"), ("string", '"a"')):
                with self.subTest(operator=operator, kind=kind):
                    with self.assertRaisesRegex(LaiCompileError, "array element must be int"):
                        self.check(f"let a: {kind}[] = [{initial}]\na[0] {operator} 1")
            with self.subTest(operator=operator):
                with self.assertRaisesRegex(LaiCompileError, "value must be int, got string"):
                    self.check(f'let a: int[] = [1]\na[0] {operator} "bad"')

    def test_all_assignments_reuse_index_type_and_bounds_checks(self):
        for operator in ("=", "+=", "-=", "*=", "/=", "%="):
            for index, error in (("-1", "index -1, length 1"), ("1", "index 1, length 1"),
                                 ("true", "array index must be int, got bool"),
                                 ('"0"', "array index must be int, got string")):
                with self.subTest(operator=operator, index=index):
                    with self.assertRaisesRegex(LaiCompileError, error):
                        self.check(f"let a: int[] = [1]\na[{index}] {operator} 2")
        with self.assertRaisesRegex(LaiCompileError, "index 0, length 0"):
            self.check("let a: int[] = []\na[0] = 1")

    def test_static_arithmetic_errors_are_rejected(self):
        for statement, error in (("a[0] /= (1 - 1)", "division by zero"),
                                 ("a[0] %= 0", "modulo by zero"),
                                 ("a[0] = 2147483647 + 1", "integer addition overflow"),
                                 ("a[0] += 2147483647 + 1", "integer addition overflow"),
                                 ("a[1 / 0] = 1", "division by zero")):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(LaiCompileError, error):
                    self.check(f"let a: int[] = [1]\n{statement}")

    def test_target_must_be_local_array(self):
        for body, error in (("a[0] = 1", "unknown variable: a"),
                            ("let a = 1\na[0] = 2", "index target must be a local array"),
                            ("let a: int[] = [1]\na[0][0] = 2", "index target must be a local array"),
                            ('("text")[0] = "a"', "index target must be a local array")):
            with self.subTest(body=body):
                with self.assertRaisesRegex(LaiCompileError, error):
                    self.check(body)

    def test_existing_scopes_and_flow_apply(self):
        self.check("let a: int[] = [1]\nif true {\na[0] += 2\n}\n"
                   "while a[0] < 5 {\na[0] += 1\n}\nfor i from 0 to 1 {\na[i] = i\n}")
        with self.assertRaisesRegex(LaiCompileError, "unknown variable: a"):
            self.check("if true {\nlet a: int[] = [1]\n}\na[0] = 2")
        with self.assertRaisesRegex(LaiCompileError, "line 5: unreachable statement"):
            check_program(parse_source("fn f() -> int {\nlet a: int[] = [1]\na[0] = 2\nreturn a[0]\na[0] = 3\n}\nfn main() {\n}"))

    def test_missing_rhs_and_assignment_expressions_remain_invalid(self):
        for body in ("a[0] =", "a[0] +=", "a[0] = a[1] = 2", "print(a[0] = 2)", "a[0]++"):
            with self.subTest(body=body):
                with self.assertRaises(LaiCompileError):
                    parse_source(program(body))

    def test_whole_array_assignment_remains_unsupported(self):
        with self.assertRaisesRegex(LaiCompileError, "whole-array assignment is not supported"):
            self.check("let a: int[] = [1]\na[0] = 2\na = [3]")

    def test_invalid_ast_operator_is_rejected(self):
        node = getattr(lai_ast, "IndexAssignStmt", None)
        self.assertIsNotNone(node)
        parsed = parse_source(program("let a: int[] = [1]"))
        parsed.statements.append(node(lai_ast.IndexExpr(lai_ast.NameExpr("a"), lai_ast.IntExpr(0), 3),
                                      "&=", lai_ast.IntExpr(1), 3))
        with self.assertRaisesRegex(LaiCompileError, "unsupported array assignment operator"):
            check_program(parsed)

    def test_c_output_uses_pointer_and_checked_arithmetic(self):
        code = compile_source(program("let a: int[] = [1]\nlet i = 0\na[i] += 2"))
        self.assertIn("int* __lai_internal_array_slot_", code)
        self.assertIn("= &__lai_internal_array_storage_", code)
        self.assertIn("__lai_internal_i32_add(", code)
        self.assertIn("__lai_internal_array_index(i, 1, 4)", code)

    def test_llvm_preserves_capability_boundary_and_checks_first(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2: LLVM backend does not support LetStmt yet"):
            compile_source(program("let a: int[] = [1]\na[0] = 2"), backend=LLVM_BACKEND)
        with self.assertRaisesRegex(LaiCompileError, "array index out of bounds"):
            compile_source(program("let a: int[] = [1]\na[1] = 2"), backend=LLVM_BACKEND)


if __name__ == "__main__":
    unittest.main()
