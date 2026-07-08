import unittest

import lai_c_backend
import lai_checker
import lai_compiler
from lai_ast import (
    AddExpr,
    BoolExpr,
    CallStmt,
    CompareExpr,
    FunctionDef,
    IfStmt,
    IntExpr,
    LetStmt,
    NameExpr,
    PrintStmt,
    Program,
    StringExpr,
)


class LaiAstTests(unittest.TestCase):
    def test_compiler_reexports_ast_nodes(self):
        self.assertIs(lai_compiler.Program, Program)
        self.assertIs(lai_compiler.LetStmt, LetStmt)
        self.assertIs(lai_compiler.PrintStmt, PrintStmt)
        self.assertIs(lai_compiler.StringExpr, StringExpr)
        self.assertIs(lai_compiler.IntExpr, IntExpr)

    def test_parser_builds_shared_ast_nodes(self):
        program = lai_compiler.parse_source("""fn greet() {
    print("hi")
}

fn main() {
    let count = 1 + 2
    let ready = count == 3
    if ready {
        greet()
    }
}""")

        self.assertIsInstance(program, Program)
        self.assertIsInstance(program.functions[0], FunctionDef)
        self.assertIsInstance(program.functions[0].statements[0], PrintStmt)
        self.assertIsInstance(program.statements[0], LetStmt)
        self.assertIsInstance(program.statements[0].value, AddExpr)
        self.assertIsInstance(program.statements[1].value, CompareExpr)
        self.assertIsInstance(program.statements[1].value.left, NameExpr)
        self.assertIsInstance(program.statements[1].value.right, IntExpr)
        self.assertIsInstance(program.statements[2], IfStmt)
        self.assertIsInstance(program.statements[2].condition, NameExpr)
        self.assertIsInstance(program.statements[2].statements[0], CallStmt)
        self.assertIsNone(program.statements[2].else_statements)

    def test_parser_builds_else_branch_nodes(self):
        program = lai_compiler.parse_source("""fn main() {
    if false {
        print("then")
    } else {
        print("else")
    }
}""")

        statement = program.statements[0]
        self.assertIsInstance(statement, IfStmt)
        self.assertIsInstance(statement.condition, BoolExpr)
        self.assertIsInstance(statement.statements[0], PrintStmt)
        self.assertIsInstance(statement.else_statements[0], PrintStmt)

    def test_checker_and_backend_import_shared_ast_nodes(self):
        self.assertIs(lai_checker.LetStmt, LetStmt)
        self.assertIs(lai_checker.BoolExpr, BoolExpr)
        self.assertIs(lai_c_backend.PrintStmt, PrintStmt)
        self.assertIs(lai_c_backend.StringExpr, StringExpr)


if __name__ == "__main__":
    unittest.main()
