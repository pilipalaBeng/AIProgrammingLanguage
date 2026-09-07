import unittest
from dataclasses import FrozenInstanceError, fields

import lai_ast
import lai_compiler
from lai_ast import (
    AddExpr,
    BoolExpr,
    CallExpr,
    CompareExpr,
    Expr,
    GroupExpr,
    IntExpr,
    LetStmt,
    LogicalExpr,
    LogicalNotExpr,
    MultiplyExpr,
    NameExpr,
    StringExpr,
    UnaryExpr,
)
from lai_compiler import LaiCompileError, parse_source, tokenize


class LaiArrayParserTests(unittest.TestCase):
    def parse_statement(self, source):
        try:
            return parse_source(f"fn main() {{\n    {source}\n}}").statements[0]
        except LaiCompileError as exc:
            self.fail(f"parser rejected valid syntax: {exc}")

    def test_array_nodes_have_exact_fields_and_compatibility_exports(self):
        for name, field_names in (
            ("ArrayExpr", ["elements", "line"]),
            ("IndexExpr", ["target", "index", "line"]),
        ):
            with self.subTest(node=name):
                node_type = getattr(lai_ast, name, None)
                self.assertIsNotNone(node_type)
                self.assertTrue(issubclass(node_type, Expr))
                self.assertEqual([field.name for field in fields(node_type)], field_names)
                self.assertIs(getattr(lai_compiler, name, None), node_type)

    def test_array_nodes_are_frozen(self):
        for name, args in (
            ("ArrayExpr", ([IntExpr(1)], 2)),
            ("IndexExpr", (NameExpr("a"), IntExpr(0), 2)),
        ):
            with self.subTest(node=name):
                node_type = getattr(lai_ast, name, None)
                self.assertIsNotNone(node_type)
                node = node_type(*args)
                with self.assertRaises(FrozenInstanceError):
                    node.line = 3

    def test_let_preserves_old_positional_constructor(self):
        self.assertEqual(
            [field.name for field in fields(LetStmt)],
            ["name", "value", "line", "type_name"],
        )
        statement = LetStmt("count", IntExpr(1), 2)
        self.assertIsNone(statement.type_name)
        self.assertEqual(self.parse_statement("let count = 1"), statement)
        self.assertEqual(LetStmt("a", IntExpr(1), 2, "int[]").type_name, "int[]")

    def test_tokenize_brackets_with_source_positions(self):
        try:
            tokens = tokenize("\n []")
        except LaiCompileError as exc:
            self.fail(f"bracket tokens are missing: {exc}")
        self.assertEqual(
            [(t.kind, t.value, t.line, t.column) for t in tokens[1:-1]],
            [("LBRACKET", "[", 2, 2), ("RBRACKET", "]", 2, 3)],
        )

    def test_parse_explicit_array_declarations(self):
        for type_name, literal, elements in (
            ("int[]", "[1, 2]", [IntExpr(1), IntExpr(2)]),
            ("string[]", '["LAI", "LingYu"]', [StringExpr("LAI"), StringExpr("LingYu")]),
            ("bool[]", "[true, false]", [BoolExpr(True), BoolExpr(False)]),
        ):
            with self.subTest(type_name=type_name):
                statement = self.parse_statement(f"let a: {type_name} = {literal}")
                self.assertEqual(statement, LetStmt("a", lai_ast.ArrayExpr(elements, 2), 2, type_name))

    def test_parse_empty_arrays(self):
        for type_name in ("int[]", "string[]", "bool[]"):
            with self.subTest(type_name=type_name):
                statement = self.parse_statement(f"let empty: {type_name} = []")
                self.assertEqual(statement.value, lai_ast.ArrayExpr([], 2))
                self.assertEqual(statement.type_name, type_name)

    def test_array_elements_keep_full_expressions_and_source_order(self):
        statement = self.parse_statement(
            'let a: int[] = [first(), 1 + 2 * 3, not ready or "a" == "b", a[0]]'
        )
        self.assertEqual(statement.value.elements, [
            CallExpr("first", None, 2),
            AddExpr([IntExpr(1), MultiplyExpr([IntExpr(2), IntExpr(3)])]),
            LogicalExpr(LogicalNotExpr(NameExpr("ready")), "or", CompareExpr(StringExpr("a"), "==", StringExpr("b"))),
            lai_ast.IndexExpr(NameExpr("a"), IntExpr(0), 2),
        ])

    def test_index_precedes_unary_and_multiplication(self):
        value = self.parse_statement("print(-a[0] * 2)").value
        self.assertEqual(value, MultiplyExpr([
            UnaryExpr("-", lai_ast.IndexExpr(NameExpr("a"), IntExpr(0), 2)),
            IntExpr(2),
        ]))

    def test_index_accepts_arithmetic_and_nested_index(self):
        value = self.parse_statement("print(a[1 + offsets[0] * 2])").value
        self.assertEqual(value, lai_ast.IndexExpr(
            NameExpr("a"),
            AddExpr([IntExpr(1), MultiplyExpr([
                lai_ast.IndexExpr(NameExpr("offsets"), IntExpr(0), 2), IntExpr(2),
            ])]),
            2,
        ))

    def test_grouped_array_name_can_be_indexed(self):
        value = self.parse_statement("print((a)[0])").value
        self.assertEqual(value, lai_ast.IndexExpr(GroupExpr(NameExpr("a")), IntExpr(0), 2))

    def test_any_primary_can_be_an_index_target_before_checking(self):
        for source, target in (
            ("1", IntExpr(1)),
            ('"text"', StringExpr("text")),
            ("true", BoolExpr(True)),
            ("false", BoolExpr(False)),
            ("make()", CallExpr("make", None, 2)),
            ("(1 + 2)", GroupExpr(AddExpr([IntExpr(1), IntExpr(2)]))),
        ):
            with self.subTest(target=source):
                value = self.parse_statement(f"print({source}[0])").value
                self.assertEqual(value, lai_ast.IndexExpr(target, IntExpr(0), 2))
        value = self.parse_statement("print([1, 2][0])").value
        self.assertEqual(value.target, lai_ast.ArrayExpr([IntExpr(1), IntExpr(2)], 2))

    def test_chained_indices_remain_nested_nodes_for_checker(self):
        value = self.parse_statement("print(a[0][1])").value
        self.assertEqual(value, lai_ast.IndexExpr(
            lai_ast.IndexExpr(NameExpr("a"), IntExpr(0), 2), IntExpr(1), 2,
        ))

    def test_index_allows_full_expressions_in_compound_assignments(self):
        for operator in ("+=", "-=", "*=", "/=", "%="):
            for index in ('"bad"', 'not ("a" == "b") or ready', 'choose("a", 1 + 1)'):
                with self.subTest(operator=operator, index=index):
                    statement = self.parse_statement(f"count {operator} a[{index}]")
                    self.assertIsInstance(statement.value, lai_ast.IndexExpr)
                    expected = self.parse_statement(f"print({index})").value
                    self.assertEqual(statement.value.index, expected)

    def test_index_allows_strings_inside_for_range_expressions(self):
        statement = self.parse_statement(
            'for i from a["start"] to a["end"] step a["step"] {\n    }'
        )
        for value, index in ((statement.start, "start"), (statement.end, "end"), (statement.step, "step")):
            self.assertEqual(value, lai_ast.IndexExpr(NameExpr("a"), StringExpr(index), 2))

    def test_parser_leaves_array_literal_positions_to_checker(self):
        for source in (
            "let a = [1]",
            "let a: int[] = ([1])",
            "a = [1]",
            "a += [1]",
            "print([1])",
            "show([1])",
            "return [1]",
            "if [1] {\n    }",
            "while [1] {\n    }",
        ):
            with self.subTest(source=source):
                self.parse_statement(source)

    def test_parser_preserves_type_strings_for_checker(self):
        for type_name in ("int", "unknown[]", "int[][]", "bool[][][]"):
            with self.subTest(type_name=type_name):
                statement = self.parse_statement(f"let a: {type_name} = [[1]]")
                self.assertEqual(statement.type_name, type_name)
                self.assertEqual(statement.value.elements, [lai_ast.ArrayExpr([IntExpr(1)], 2)])

    def test_type_brackets_allow_spaces(self):
        statement = self.parse_statement("let a: int [ ] [ ] = []")
        self.assertEqual(statement.type_name, "int[][]")

    def test_array_parameter_and_return_types_reach_checker(self):
        for type_name in ("int[]", "string[]", "bool[]", "int[][]"):
            with self.subTest(type_name=type_name):
                source = f"fn identity(a: {type_name}) -> {type_name} {{\n    return a\n}}\nfn main() {{\n}}"
                try:
                    program = parse_source(source)
                except LaiCompileError as exc:
                    self.fail(f"array signature did not reach checker: {exc}")
                self.assertEqual(program.functions[0].params[0].type_name, type_name)
                self.assertEqual(program.functions[0].return_type, type_name)

    def test_keyword_compatible_names_support_array_declarations_and_reads(self):
        for name in ("fn", "main", "let", "print"):
            with self.subTest(name=name):
                statement = self.parse_statement(f"let {name}: int[] = [1]")
                self.assertEqual(statement.name, name)
                value = self.parse_statement(f"print({name}[0])").value
                self.assertEqual(value.target, NameExpr(name))

    def test_array_element_assignments_have_shared_ast(self):
        for target in (
            "a[0]", "a[1 + offsets[0]]", "a[0][1]", "(a)[0]",
            "fn[0]", "main[0]", "let[0]", "print[0]",
        ):
            for operator in ("=", "+=", "-=", "*=", "/=", "%="):
                with self.subTest(target=target, operator=operator):
                    statement = parse_source(f"fn main() {{\n    // assignment\n    {target} {operator} 1\n}}").statements[0]
                    self.assertIsInstance(statement, lai_ast.IndexAssignStmt)
                    expected = parse_source(f"fn main() {{\n    // read\n    print({target})\n}}").statements[0].value
                    self.assertEqual(statement.target, expected)
                    self.assertEqual(statement.operator, operator)
                    self.assertEqual(statement.value, IntExpr(1))
                    self.assertEqual(statement.line, 3)

    def test_missing_array_delimiters_and_elements_are_rejected(self):
        for statement, error in (
            ("let a: int[] = [1, 2", "expected RBRACKET"),
            ("let a: int[] = [1 2]", "expected RBRACKET"),
            ("let a: int[] = [,1]", "expected expression"),
            ("let a: int[] = [1,,2]", "expected expression"),
            ("let a: int[ = [1]", "expected RBRACKET"),
            ("let a: = [1]", "expected IDENT"),
            ("print(a[0)", "expected RBRACKET"),
            ("print(a[])", "expected expression"),
            ("print(a[0, 1])", "expected RBRACKET"),
        ):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(LaiCompileError, f"line 2.*{error}"):
                    parse_source(f"fn main() {{\n    {statement}\n}}")

    def test_array_trailing_commas_are_rejected(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2.*expected expression"):
            parse_source("fn main() {\n    let a: int[] = [1,]\n}")

    def test_array_expressions_and_types_remain_single_line(self):
        for statement, error in (
            ("let a: int[] = [\n1]", "expected expression"),
            ("let a: int[] = [1,\n2]", "expected expression"),
            ("let a: int[] = [1\n]", "expected RBRACKET"),
            ("let a: int[\n] = []", "expected RBRACKET"),
            ("print(a[\n0])", "expected expression"),
            ("print(a[0\n])", "expected RBRACKET"),
        ):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(LaiCompileError, f"line 2.*{error}"):
                    parse_source(f"fn main() {{\n    {statement}\n}}")


if __name__ == "__main__":
    unittest.main()
