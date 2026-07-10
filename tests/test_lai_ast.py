import unittest

import lai_c_backend
import lai_checker
import lai_compiler
from lai_ast import (
    AddExpr,
    AssignStmt,
    BoolExpr,
    BreakStmt,
    CallExpr,
    CallStmt,
    CompareExpr,
    ContinueStmt,
    ForStmt,
    FunctionDef,
    GroupExpr,
    IfStmt,
    IntExpr,
    LetStmt,
    MinusAssignStmt,
    MultiplyAssignStmt,
    MultiplyExpr,
    NameExpr,
    Param,
    PlusAssignStmt,
    PrintStmt,
    Program,
    ReturnStmt,
    StringExpr,
    SubtractExpr,
    WhileStmt,
)


class LaiAstTests(unittest.TestCase):
    def test_compiler_reexports_ast_nodes(self):
        self.assertIs(lai_compiler.Program, Program)
        self.assertIs(lai_compiler.LetStmt, LetStmt)
        self.assertIs(lai_compiler.PrintStmt, PrintStmt)
        self.assertIs(lai_compiler.Param, Param)
        self.assertIs(lai_compiler.ReturnStmt, ReturnStmt)
        self.assertIs(lai_compiler.CallExpr, CallExpr)
        self.assertIs(lai_compiler.AssignStmt, AssignStmt)
        self.assertIs(lai_compiler.WhileStmt, WhileStmt)
        self.assertIs(lai_compiler.ForStmt, ForStmt)
        self.assertIs(lai_compiler.GroupExpr, GroupExpr)
        self.assertIs(lai_compiler.SubtractExpr, SubtractExpr)
        self.assertIs(lai_compiler.MultiplyExpr, MultiplyExpr)
        self.assertIs(lai_compiler.MultiplyAssignStmt, MultiplyAssignStmt)
        self.assertIs(lai_compiler.MinusAssignStmt, MinusAssignStmt)
        self.assertIs(lai_compiler.PlusAssignStmt, PlusAssignStmt)
        self.assertIs(lai_compiler.BreakStmt, BreakStmt)
        self.assertIs(lai_compiler.ContinueStmt, ContinueStmt)
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

    def test_parser_builds_else_if_as_nested_if_node(self):
        program = lai_compiler.parse_source("""fn main() {
    if false {
        print("A")
    } else if true {
        print("B")
    } else {
        print("C")
    }
}""")

        outer_if = program.statements[0]
        self.assertIsInstance(outer_if, IfStmt)
        nested_if = outer_if.else_statements[0]
        self.assertIsInstance(nested_if, IfStmt)
        self.assertIsInstance(nested_if.condition, BoolExpr)
        self.assertIsInstance(nested_if.statements[0], PrintStmt)
        self.assertIsInstance(nested_if.else_statements[0], PrintStmt)

    def test_checker_and_backend_import_shared_ast_nodes(self):
        self.assertIs(lai_checker.LetStmt, LetStmt)
        self.assertIs(lai_checker.BoolExpr, BoolExpr)
        self.assertIs(lai_c_backend.PrintStmt, PrintStmt)
        self.assertIs(lai_c_backend.StringExpr, StringExpr)
        self.assertIs(lai_checker.ReturnStmt, ReturnStmt)
        self.assertIs(lai_c_backend.CallExpr, CallExpr)
        self.assertIs(lai_checker.AssignStmt, AssignStmt)
        self.assertIs(lai_c_backend.WhileStmt, WhileStmt)
        self.assertIs(lai_checker.ForStmt, ForStmt)
        self.assertIs(lai_c_backend.ForStmt, ForStmt)
        self.assertIs(lai_checker.GroupExpr, GroupExpr)
        self.assertIs(lai_c_backend.GroupExpr, GroupExpr)
        self.assertIs(lai_checker.SubtractExpr, SubtractExpr)
        self.assertIs(lai_c_backend.SubtractExpr, SubtractExpr)
        self.assertIs(lai_checker.MultiplyExpr, MultiplyExpr)
        self.assertIs(lai_c_backend.MultiplyExpr, MultiplyExpr)
        self.assertIs(lai_checker.MultiplyAssignStmt, MultiplyAssignStmt)
        self.assertIs(lai_c_backend.MultiplyAssignStmt, MultiplyAssignStmt)
        self.assertIs(lai_checker.MinusAssignStmt, MinusAssignStmt)
        self.assertIs(lai_c_backend.MinusAssignStmt, MinusAssignStmt)
        self.assertIs(lai_checker.PlusAssignStmt, PlusAssignStmt)
        self.assertIs(lai_c_backend.PlusAssignStmt, PlusAssignStmt)
        self.assertIs(lai_checker.BreakStmt, BreakStmt)
        self.assertIs(lai_c_backend.BreakStmt, BreakStmt)
        self.assertIs(lai_checker.ContinueStmt, ContinueStmt)
        self.assertIs(lai_c_backend.ContinueStmt, ContinueStmt)


if __name__ == "__main__":
    unittest.main()
