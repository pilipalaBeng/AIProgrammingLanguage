import contextlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import lai_compiler
from lai_c_backend import C_BACKEND
from lai_llvm_backend import LLVM_BACKEND
from lai_compiler import (
    AddExpr,
    AssignStmt,
    BoolExpr,
    BreakStmt,
    CallExpr,
    CompareExpr,
    ContinueStmt,
    DivideAssignStmt,
    DivideExpr,
    ForStmt,
    GroupExpr,
    IfStmt,
    IntExpr,
    LaiCompileError,
    LetStmt,
    LogicalExpr,
    LogicalNotExpr,
    MinusAssignStmt,
    ModuloAssignStmt,
    ModuloExpr,
    MultiplyAssignStmt,
    MultiplyExpr,
    NameExpr,
    PrintStmt,
    Program,
    ReturnStmt,
    StringExpr,
    SubtractExpr,
    Token,
    UnaryExpr,
    WhileStmt,
    compile_source,
    generate_c,
    main as compiler_main,
    parse_source,
    tokenize,
)


class LaiCompilerTests(unittest.TestCase):
    def test_tokenize_main_program(self):
        source = '''fn main() {
    let name = "JD"
    print(name)
}'''

        tokens = tokenize(source)
        pairs = [(token.kind, token.value) for token in tokens]

        self.assertEqual(
            pairs,
            [
                ("FN", "fn"),
                ("MAIN", "main"),
                ("LPAREN", "("),
                ("RPAREN", ")"),
                ("LBRACE", "{"),
                ("NEWLINE", "\n"),
                ("LET", "let"),
                ("IDENT", "name"),
                ("EQUAL", "="),
                ("STRING", "JD"),
                ("NEWLINE", "\n"),
                ("PRINT", "print"),
                ("LPAREN", "("),
                ("IDENT", "name"),
                ("RPAREN", ")"),
                ("NEWLINE", "\n"),
                ("RBRACE", "}"),
                ("EOF", ""),
            ],
        )
        self.assertEqual(tokens[6], Token("LET", "let", 2, 5))
        self.assertEqual(tokens[9], Token("STRING", "JD", 2, 16))

    def test_tokenize_rejects_unknown_character(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2, column 5"):
            tokenize("fn main() {\n    @\n}")

    def test_tokenize_complete_comparison_operators(self):
        cases = [
            ("<", "LT"),
            ("<=", "LT_EQUAL"),
            (">", "GT"),
            (">=", "GT_EQUAL"),
            ("==", "EQUAL_EQUAL"),
            ("!=", "BANG_EQUAL"),
        ]

        for source, expected_kind in cases:
            with self.subTest(source=source):
                token = tokenize(source)[0]
                self.assertEqual((token.kind, token.value), (expected_kind, source))

    def test_tokenize_boolean_logic_keywords(self):
        tokens = tokenize("and or not")
        self.assertEqual(
            [(token.kind, token.value) for token in tokens[:-1]],
            [("AND", "and"), ("OR", "or"), ("NOT", "not")],
        )

    def test_symbolic_boolean_logic_remains_unsupported(self):
        cases = [
            ("true && false", r"unexpected character: &"),
            ("true || false", r"unexpected character: \|"),
            ("!true", r"unexpected character: !"),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(LaiCompileError, error):
                    tokenize(source)

    def test_tokenize_return_type_and_return_statement(self):
        source = """fn add(a: int) -> int {
    return a
}"""

        tokens = tokenize(source)

        self.assertIn(Token("ARROW", "->", 1, 16), tokens)
        self.assertIn(Token("RETURN", "return", 2, 5), tokens)

    def test_tokenize_for_loop_keywords(self):
        tokens = tokenize("""fn main() {
    for i from 0 to 3 {
        print(i)
    }
}""")

        self.assertIn(Token("FOR", "for", 2, 5), tokens)
        self.assertIn(Token("FROM", "from", 2, 11), tokens)
        self.assertIn(Token("TO", "to", 2, 18), tokens)

    def test_tokenize_for_step_keyword(self):
        tokens = tokenize("""fn main() {
    for i from 0 to 6 step 2 {
        print(i)
    }
}""")

        self.assertIn(Token("STEP", "step", 2, 23), tokens)

    def test_tokenize_for_through_keyword(self):
        tokens = tokenize("""fn main() {
    for i from 0 through 3 {
        print(i)
    }
}""")

        self.assertIn(Token("THROUGH", "through", 2, 18), tokens)

    def test_tokenize_plus_assignment(self):
        tokens = tokenize("""fn main() {
    let count = 0
    count += 1
}""")

        self.assertIn(Token("PLUS_EQUAL", "+=", 3, 11), tokens)

    def test_tokenize_minus_assignment(self):
        tokens = tokenize("""fn main() {
    let count = 3
    count -= 1
}""")

        self.assertIn(Token("MINUS_EQUAL", "-=", 3, 11), tokens)

    def test_tokenize_multiply_assignment(self):
        tokens = tokenize("""fn main() {
    let count = 3
    count *= 2
}""")

        self.assertIn(Token("STAR_EQUAL", "*=", 3, 11), tokens)

    def test_tokenize_divide_assignment(self):
        tokens = tokenize("""fn main() {
    let count = 8
    count /= 2
}""")

        self.assertIn(Token("SLASH_EQUAL", "/=", 3, 11), tokens)

    def test_tokenize_modulo_assignment(self):
        tokens = tokenize("""fn main() {
    let count = 7
    count %= 3
}""")

        self.assertIn(Token("PERCENT_EQUAL", "%=", 3, 11), tokens)

    def test_divide_assignment_text_inside_comment_is_ignored(self):
        tokens = tokenize("""fn main() {
    // count /= 2
    print(8 / 2)
}""")

        pairs = [(token.kind, token.value) for token in tokens]
        self.assertNotIn(("SLASH_EQUAL", "/="), pairs)
        self.assertIn(("SLASH", "/"), pairs)

    def test_tokenize_multiplication(self):
        tokens = tokenize("""fn main() {
    print(2 * 3)
}""")

        self.assertIn(Token("STAR", "*", 2, 13), tokens)

    def test_tokenize_division(self):
        tokens = tokenize("""fn main() {
    print(8 / 2)
}""")

        self.assertIn(Token("SLASH", "/", 2, 13), tokens)

    def test_tokenize_modulo(self):
        tokens = tokenize("""fn main() {
    print(7 % 3)
}""")

        self.assertIn(Token("PERCENT", "%", 2, 13), tokens)

    def test_cli_help_uses_ly_source_extension(self):
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(output):
                compiler_main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("Compile LAI v0.35 source", help_text)
        self.assertIn(".ly source file", help_text)
        self.assertIn("--backend {c,llvm}", help_text)
        self.assertNotIn(".lai source file", help_text)

    def test_basic_comparisons_example_compiles(self):
        example_path = (
            Path(__file__).resolve().parents[1] / "examples" / "basic_comparisons.ly"
        )
        c_code = compile_source(example_path.read_text(encoding="utf-8"))

        self.assertIn('printf("%d\\n", 2 <= 2);', c_code)
        self.assertIn('printf("%d\\n", 1 != 2);', c_code)
        self.assertIn('strcmp("LAI", "LAI") == 0', c_code)
        self.assertIn('strcmp("LAI", "C") != 0', c_code)

    def test_cli_defaults_to_c_backend(self):
        with patch("lai_compiler.compile_file") as compile_file:
            compile_file.return_value = (Path("build/sample.c"), Path("build/sample.exe"))
            result = compiler_main(["sample.ly"])

        self.assertEqual(result, 0)
        compile_file.assert_called_once_with(Path("sample.ly"), Path("build"), C_BACKEND)

    def test_cli_selects_explicit_c_backend(self):
        with patch("lai_compiler.compile_file") as compile_file:
            compile_file.return_value = (Path("build/sample.c"), Path("build/sample.exe"))
            result = compiler_main(["sample.ly", "--backend", "c"])

        self.assertEqual(result, 0)
        compile_file.assert_called_once_with(Path("sample.ly"), Path("build"), C_BACKEND)

    def test_cli_selects_llvm_backend(self):
        with patch("lai_compiler.compile_file") as compile_file:
            compile_file.return_value = (Path("build/sample.ll"), Path("build/sample.exe"))
            result = compiler_main(["sample.ly", "--backend", "llvm"])

        self.assertEqual(result, 0)
        compile_file.assert_called_once_with(Path("sample.ly"), Path("build"), LLVM_BACKEND)

    def test_cli_rejects_unknown_backend(self):
        with self.assertRaises(SystemExit) as raised:
            compiler_main(["sample.ly", "--backend", "unknown"])

        self.assertEqual(raised.exception.code, 2)

    def test_parse_source_builds_ast(self):
        source = '''fn main() {
    let name = "JD"
    let count = 123
    print(name)
}'''

        program = parse_source(source)

        self.assertEqual(
            program,
            Program(
                statements=[
                    LetStmt("name", StringExpr("JD"), 2),
                    LetStmt("count", IntExpr(123), 3),
                    PrintStmt(NameExpr("name"), 4),
                ]
            ),
        )

    def test_check_program_accepts_valid_program(self):
        program = parse_source("""fn greet() {
    print("Hello")
}

fn main() {
    let count = 1 + 2
    let ready = count == 3
    if ready {
        greet()
    }
}""")

        self.assertIsNone(lai_compiler.check_program(program))

    def test_parse_source_rejects_missing_main_parentheses(self):
        with self.assertRaisesRegex(LaiCompileError, "expected LPAREN"):
            parse_source("fn main {\n}")

    def test_generate_c_from_ast(self):
        program = Program(
            statements=[
                PrintStmt(StringExpr("Hello LAI"), 1),
                LetStmt("name", StringExpr("JD"), 2),
                PrintStmt(NameExpr("name"), 3),
                LetStmt("count", IntExpr(123), 4),
                PrintStmt(NameExpr("count"), 5),
            ]
        )

        c_code = generate_c(program)

        self.assertIn('printf("Hello LAI\\n");', c_code)
        self.assertIn('const char* name = "JD";', c_code)
        self.assertIn('printf("%s\\n", name);', c_code)
        self.assertIn("int count = 123;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_generate_c_rejects_duplicate_variable(self):
        program = Program(
            statements=[
                LetStmt("name", StringExpr("A"), 2),
                LetStmt("name", StringExpr("B"), 3),
            ]
        )

        with self.assertRaisesRegex(LaiCompileError, "variable already defined"):
            generate_c(program)

    def test_print_literal_and_string_variable(self):
        source = '''fn main() {
    print("Hello LAI")
    let name = "LingYu"
    print(name)
}'''

        c_code = compile_source(source)

        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn('printf("Hello LAI\\n");', c_code)
        self.assertIn('const char* name = "LingYu";', c_code)
        self.assertIn('printf("%s\\n", name);', c_code)

    def test_integer_variable(self):
        source = '''fn main() {
    let count = 123
    print(count)
}'''

        c_code = compile_source(source)

        self.assertIn("int count = 123;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_rejects_unknown_variable(self):
        source = '''fn main() {
    print(name)
}'''

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable"):
            compile_source(source)

    def test_rejects_invalid_variable_name(self):
        source = '''fn main() {
    let 1name = 123
}'''

        with self.assertRaisesRegex(LaiCompileError, "line 2.*invalid variable name"):
            compile_source(source)

    def test_rejects_missing_main(self):
        with self.assertRaisesRegex(LaiCompileError, "line 1.*expected FN"):
            compile_source('print("Hello")')

    def test_preserves_keyword_variable_names(self):
        source = '''fn main() {
    let print = 123
    print(print)
    let main = "M"
    print(main)
}'''

        c_code = compile_source(source)

        self.assertIn("int print = 123;", c_code)
        self.assertIn('printf("%d\\n", print);', c_code)
        self.assertIn('const char* main = "M";', c_code)
        self.assertIn('printf("%s\\n", main);', c_code)

    def test_boolean_logic_keywords_are_reserved_names(self):
        cases = [
            ("fn main() {\n    let and = true\n}", "invalid variable name"),
            ("fn show(or: bool) {\n}\nfn main() {\n}", "invalid parameter name"),
            ("fn not() {\n}\nfn main() {\n}", "expected IDENT"),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(LaiCompileError, error):
                    parse_source(source)

    def test_rejects_single_line_empty_block(self):
        with self.assertRaisesRegex(LaiCompileError, "expected NEWLINE"):
            compile_source("fn main() {}")

    def test_rejects_statement_closed_without_newline(self):
        with self.assertRaisesRegex(LaiCompileError, "expected NEWLINE"):
            compile_source('fn main() {\n    print("A")}')

    def test_preserves_python_style_string_escapes(self):
        source = '''fn main() {
    print("\\x42")
    let name = "\\u004a"
    print(name)
    print("a\\"b")
}'''

        c_code = compile_source(source)

        self.assertIn('printf("B\\n");', c_code)
        self.assertIn('const char* name = "J";', c_code)
        self.assertIn('printf("a\\"b\\n");', c_code)

    def test_print_integer_literal(self):
        c_code = compile_source("""fn main() {
    print(123)
}""")

        self.assertIn('printf("%d\\n", 123);', c_code)

    def test_ignores_line_comments(self):
        c_code = compile_source("""fn main() {
    // greet from LAI
    print("Hello") // trailing comment
}""")

        self.assertIn('printf("Hello\\n");', c_code)

    def test_print_integer_addition(self):
        c_code = compile_source("""fn main() {
    print(1 + 2 + 3)
}""")

        self.assertIn('printf("%d\\n", 1 + 2 + 3);', c_code)

    def test_let_integer_addition(self):
        c_code = compile_source("""fn main() {
    let count = 1 + 2 + 3
    print(count)
}""")

        self.assertIn("int count = 1 + 2 + 3;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_print_integer_subtraction(self):
        c_code = compile_source("""fn main() {
    print(5 - 2)
}""")

        self.assertIn('printf("%d\\n", 5 - 2);', c_code)

    def test_print_integer_multiplication(self):
        c_code = compile_source("""fn main() {
    print(2 * 3)
}""")

        self.assertIn('printf("%d\\n", 2 * 3);', c_code)

    def test_let_integer_subtraction(self):
        c_code = compile_source("""fn main() {
    let count = 5 - 2
    print(count)
}""")

        self.assertIn("int count = 5 - 2;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_let_integer_multiplication(self):
        c_code = compile_source("""fn main() {
    let count = 2 * 3
    print(count)
}""")

        self.assertIn("int count = 2 * 3;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_print_integer_division(self):
        c_code = compile_source("""fn main() {
    print(8 / 2)
}""")

        self.assertIn('printf("%d\\n", 8 / 2);', c_code)

    def test_print_integer_modulo(self):
        c_code = compile_source("""fn main() {
    print(7 % 3)
}""")

        self.assertIn('printf("%d\\n", 7 % 3);', c_code)

    def test_let_integer_division(self):
        c_code = compile_source("""fn main() {
    let count = 8 / 2
    print(count)
}""")

        self.assertIn("int count = 8 / 2;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_let_integer_modulo(self):
        c_code = compile_source("""fn main() {
    let remainder = 7 % 3
    print(remainder)
}""")

        self.assertIn("int remainder = 7 % 3;", c_code)
        self.assertIn('printf("%d\\n", remainder);', c_code)

    def test_subtraction_can_use_names_calls_and_return_values(self):
        c_code = compile_source("""fn diff(a: int, b: int) -> int {
    return a - b
}

fn show(value: int) {
    print(value)
}

fn main() {
    let count = diff(5, 2)
    show(count - 1)
}""")

        self.assertIn("return a - b;", c_code)
        self.assertIn("int count = diff(5, 2);", c_code)
        self.assertIn("show(count - 1);", c_code)

    def test_subtraction_composes_with_parentheses_addition_and_comparison(self):
        c_code = compile_source("""fn main() {
    let count = (5 + 2) - 1
    let ok = (count - 3) == 3
    if ok {
        print(count - 1)
    }
}""")

        self.assertIn("int count = (5 + 2) - 1;", c_code)
        self.assertIn("int ok = (count - 3) == 3;", c_code)
        self.assertIn('printf("%d\\n", count - 1);', c_code)

    def test_multiplication_can_use_names_calls_and_return_values(self):
        c_code = compile_source("""fn double(value: int) -> int {
    return value * 2
}

fn main() {
    let count = double(3) * 4
    print(double(count * 2))
}""")

        self.assertIn("return value * 2;", c_code)
        self.assertIn("int count = double(3) * 4;", c_code)
        self.assertIn('printf("%d\\n", double(count * 2));', c_code)

    def test_multiplication_has_precedence_over_addition_and_subtraction(self):
        c_code = compile_source("""fn main() {
    print(2 + 3 * 4)
    print(10 - 2 * 3)
}""")

        self.assertIn('printf("%d\\n", 2 + 3 * 4);', c_code)
        self.assertIn('printf("%d\\n", 10 - 2 * 3);', c_code)

    def test_parentheses_override_multiplication_precedence(self):
        c_code = compile_source("""fn main() {
    print((2 + 3) * 4)
}""")

        self.assertIn('printf("%d\\n", (2 + 3) * 4);', c_code)

    def test_division_can_use_names_calls_and_return_values(self):
        c_code = compile_source("""fn half(value: int) -> int {
    return value / 2
}

fn main() {
    let count = half(8) / 2
    print(half(count / 2))
}""")

        self.assertIn("return value / 2;", c_code)
        self.assertIn("int count = half(8) / 2;", c_code)
        self.assertIn('printf("%d\\n", half(count / 2));', c_code)

    def test_division_shares_precedence_with_multiplication(self):
        c_code = compile_source("""fn main() {
    print(8 + 6 / 2)
    print(8 / 2 * 3)
}""")

        self.assertIn('printf("%d\\n", 8 + 6 / 2);', c_code)
        self.assertIn('printf("%d\\n", 8 / 2 * 3);', c_code)

    def test_parentheses_override_division_precedence(self):
        c_code = compile_source("""fn main() {
    print((6 + 4) / 2)
}""")

        self.assertIn('printf("%d\\n", (6 + 4) / 2);', c_code)

    def test_modulo_can_use_names_calls_and_return_values(self):
        c_code = compile_source("""fn remainder(value: int) -> int {
    return value % 2
}

fn main() {
    let count = remainder(7) % 2
    print(remainder(count % 2))
}""")

        self.assertIn("return value % 2;", c_code)
        self.assertIn("int count = remainder(7) % 2;", c_code)
        self.assertIn('printf("%d\\n", remainder(count % 2));', c_code)

    def test_modulo_shares_precedence_with_multiplication_and_division(self):
        c_code = compile_source("""fn main() {
    print(8 + 7 % 3)
    print(8 % 3 * 2)
    print(8 / 2 % 3)
}""")

        self.assertIn('printf("%d\\n", 8 + 7 % 3);', c_code)
        self.assertIn('printf("%d\\n", 8 % 3 * 2);', c_code)
        self.assertIn('printf("%d\\n", 8 / 2 % 3);', c_code)

    def test_parentheses_override_modulo_precedence(self):
        c_code = compile_source("""fn main() {
    print((10 + 5) % 4)
}""")

        self.assertIn('printf("%d\\n", (10 + 5) % 4);', c_code)

    def test_boolean_variable_and_print(self):
        c_code = compile_source("""fn main() {
    let ready = true
    print(ready)
}""")

        self.assertIn("int ready = 1;", c_code)
        self.assertIn('printf("%d\\n", ready);', c_code)

    def test_comparison_expression(self):
        c_code = compile_source("""fn main() {
    let ok = 1 < 2
    print(3 == 3)
    print(ok)
}""")

        self.assertIn("int ok = 1 < 2;", c_code)
        self.assertIn('printf("%d\\n", 3 == 3);', c_code)
        self.assertIn('printf("%d\\n", ok);', c_code)

    def test_comparison_can_use_integer_variable(self):
        c_code = compile_source("""fn main() {
    let count = 3
    let ok = count == 3
    if count == 3 {
        print("three")
    }
}""")

        self.assertIn("int count = 3;", c_code)
        self.assertIn("int ok = count == 3;", c_code)
        self.assertIn("if (count == 3) {", c_code)

    def test_complete_comparisons_generate_type_appropriate_c(self):
        c_code = compile_source("""fn main() {
    let low = 1 <= 2
    let high = 3 >= 2
    let different = 1 != 2
    let same_bool = true == true
    let different_bool = true != false
    let same_text = "LAI" == "LAI"
    let different_text = "LAI" != "C"
    print(low)
}""")

        self.assertIn("int low = 1 <= 2;", c_code)
        self.assertIn("int high = 3 >= 2;", c_code)
        self.assertIn("int different = 1 != 2;", c_code)
        self.assertIn("int same_bool = 1 == 1;", c_code)
        self.assertIn("int different_bool = 1 != 0;", c_code)
        self.assertIn('int same_text = strcmp("LAI", "LAI") == 0;', c_code)
        self.assertIn('int different_text = strcmp("LAI", "C") != 0;', c_code)

    def test_string_comparison_accepts_variables_parameters_and_calls(self):
        c_code = compile_source("""fn identity(value: string) -> string {
    return value
}

fn same(left: string, right: string) -> bool {
    return left == right
}

fn main() {
    let expected = "LAI"
    let actual = identity("LAI")
    print(expected == actual)
    print(identity("LAI") != expected)
    print(same(expected, actual))
}""")

        self.assertIn("return strcmp(left, right) == 0;", c_code)
        self.assertIn("strcmp(expected, actual) == 0", c_code)
        self.assertIn('strcmp(identity("LAI"), expected) != 0', c_code)
        self.assertIn("same(expected, actual)", c_code)

    def test_comparisons_work_in_all_supported_expression_positions(self):
        c_code = compile_source("""fn is_jd(name: string) -> bool {
    return name == "JD"
}

fn show(value: bool) {
    print(value)
}

fn main() {
    let count = 0
    let initial = count == 0
    let ok = false
    ok = count <= 1
    if "A" == "A" {
        show(count >= 0)
    }
    while "done" != "done" {
        print(false)
    }
    print(count != 2)
    print(is_jd("JD"))
}""")

        self.assertIn('return strcmp(name, "JD") == 0;', c_code)
        self.assertIn("int initial = count == 0;", c_code)
        self.assertIn("ok = count <= 1;", c_code)
        self.assertIn('if (strcmp("A", "A") == 0) {', c_code)
        self.assertIn("show(count >= 0);", c_code)
        self.assertIn('while (strcmp("done", "done") != 0) {', c_code)
        self.assertIn('printf("%d\\n", count != 2);', c_code)
        self.assertIn('printf("%d\\n", is_jd("JD"));', c_code)

    def test_parse_source_builds_complete_comparison_operators(self):
        operators = ("<", "<=", ">", ">=", "==", "!=")

        for operator in operators:
            with self.subTest(operator=operator):
                program = parse_source(
                    f"fn main() {{\n    print(1 {operator} 2)\n}}"
                )
                expression = program.statements[0].value
                self.assertEqual(
                    expression,
                    CompareExpr(IntExpr(1), operator, IntExpr(2)),
                )

    def test_parse_boolean_logic_precedence(self):
        value = parse_source(
            "fn main() {\n    print(not 1 < 2 or false and true)\n}"
        ).statements[0].value
        self.assertEqual(
            value,
            LogicalExpr(
                LogicalNotExpr(CompareExpr(IntExpr(1), "<", IntExpr(2))),
                "or",
                LogicalExpr(BoolExpr(False), "and", BoolExpr(True)),
            ),
        )

    def test_parse_boolean_logic_associativity_and_grouping(self):
        program = parse_source(
            "fn main() {\n"
            "    print(not not true)\n"
            "    print(true or false or true)\n"
            "    print(true and false and true)\n"
            "    print((true or false) and true)\n"
            "}"
        )
        self.assertEqual(
            program.statements[0].value,
            LogicalNotExpr(LogicalNotExpr(BoolExpr(True))),
        )
        self.assertEqual(
            program.statements[1].value,
            LogicalExpr(
                LogicalExpr(BoolExpr(True), "or", BoolExpr(False)),
                "or",
                BoolExpr(True),
            ),
        )
        self.assertEqual(
            program.statements[2].value,
            LogicalExpr(
                LogicalExpr(BoolExpr(True), "and", BoolExpr(False)),
                "and",
                BoolExpr(True),
            ),
        )
        self.assertEqual(
            program.statements[3].value,
            LogicalExpr(
                GroupExpr(LogicalExpr(BoolExpr(True), "or", BoolExpr(False))),
                "and",
                BoolExpr(True),
            ),
        )

    def test_comparison_precedence_remains_below_arithmetic(self):
        program = parse_source("""fn main() {
    print(1 + 2 * 3 >= 7)
}""")

        expression = program.statements[0].value
        self.assertEqual(
            expression,
            CompareExpr(
                AddExpr([IntExpr(1), MultiplyExpr([IntExpr(2), IntExpr(3)])]),
                ">=",
                IntExpr(7),
            ),
        )

    def test_grouped_comparison_can_participate_in_equality(self):
        program = parse_source("""fn main() {
    print((1 < 2) == true)
}""")

        expression = program.statements[0].value
        self.assertEqual(
            expression,
            CompareExpr(
                GroupExpr(CompareExpr(IntExpr(1), "<", IntExpr(2))),
                "==",
                BoolExpr(True),
            ),
        )

    def test_rejects_comparison_chains(self):
        operators = ("<", "<=", ">", ">=", "==", "!=")

        for left_operator in operators:
            for right_operator in operators:
                with self.subTest(
                    left_operator=left_operator,
                    right_operator=right_operator,
                ):
                    source = (
                        "fn main() {\n"
                        f"    print(1 {left_operator} 2 {right_operator} 3)\n"
                        "}"
                    )
                    with self.assertRaisesRegex(
                        LaiCompileError,
                        "comparison chains are not supported",
                    ):
                        parse_source(source)

    def test_separate_comparisons_can_be_combined_with_and(self):
        expression = parse_source(
            "fn main() {\n    print(1 < 2 and 2 < 3)\n}"
        ).statements[0].value
        self.assertEqual(
            expression,
            LogicalExpr(
                CompareExpr(IntExpr(1), "<", IntExpr(2)),
                "and",
                CompareExpr(IntExpr(2), "<", IntExpr(3)),
            ),
        )

    def test_rejects_incomplete_comparison_operators(self):
        operators = ("<", "<=", ">", ">=", "==", "!=")

        for operator in operators:
            with self.subTest(operator=operator):
                source = f"fn main() {{\n    print(1 {operator})\n}}"
                with self.assertRaisesRegex(LaiCompileError, "expected expression"):
                    parse_source(source)

    def test_if_statement(self):
        c_code = compile_source("""fn main() {
    if 1 < 2 {
        print("yes")
    }
}""")

        self.assertIn("if (1 < 2) {", c_code)
        self.assertIn('printf("yes\\n");', c_code)

    def test_if_else_statement(self):
        c_code = compile_source("""fn main() {
    if true {
        print("yes")
    } else {
        print("no")
    }
}""")

        self.assertIn("if (1) {", c_code)
        self.assertIn("} else {", c_code)
        self.assertIn('printf("yes\\n");', c_code)
        self.assertIn('printf("no\\n");', c_code)

    def test_if_else_allows_else_on_next_line(self):
        c_code = compile_source("""fn main() {
    if false {
        print("yes")
    }
    else {
        print("no")
    }
}""")

        self.assertIn("if (0) {", c_code)
        self.assertIn("} else {", c_code)
        self.assertIn('printf("no\\n");', c_code)

    def test_if_else_if_statement(self):
        c_code = compile_source("""fn main() {
    let score = 85
    if score > 90 {
        print("A")
    } else if score > 80 {
        print("B")
    } else {
        print("C")
    }
}""")

        self.assertIn("if (score > 90) {", c_code)
        self.assertIn("if (score > 80) {", c_code)
        self.assertIn('printf("A\\n");', c_code)
        self.assertIn('printf("B\\n");', c_code)
        self.assertIn('printf("C\\n");', c_code)

    def test_if_else_if_chain(self):
        c_code = compile_source("""fn main() {
    let score = 75
    if score > 90 {
        print("A")
    } else if score > 80 {
        print("B")
    } else if score > 70 {
        print("C")
    } else {
        print("D")
    }
}""")

        self.assertEqual(c_code.count("} else {"), 3)
        self.assertIn("if (score > 90) {", c_code)
        self.assertIn("if (score > 80) {", c_code)
        self.assertIn("if (score > 70) {", c_code)

    def test_if_can_use_boolean_variable(self):
        c_code = compile_source("""fn main() {
    let ready = true
    if ready {
        print("ready")
    }
}""")

        self.assertIn("int ready = 1;", c_code)
        self.assertIn("if (ready) {", c_code)
        self.assertIn('printf("ready\\n");', c_code)

    def test_while_loop_with_assignment(self):
        c_code = compile_source("""fn main() {
    let count = 0
    while count < 3 {
        print(count)
        count = count + 1
    }
}""")

        self.assertIn("int count = 0;", c_code)
        self.assertIn("while (count < 3) {", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)
        self.assertIn("count = count + 1;", c_code)

    def test_plus_assignment_adds_to_existing_int(self):
        c_code = compile_source("""fn main() {
    let count = 0
    count += 1
    print(count)
}""")

        self.assertIn("int count = 0;", c_code)
        self.assertIn("count = count + 1;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_plus_assignment_can_use_int_expression(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    let count = 0
    count += add(1, 2)
    print(count)
}""")

        self.assertIn("count = count + add(1, 2);", c_code)

    def test_function_parameter_can_use_plus_assignment(self):
        c_code = compile_source("""fn bump(count: int) {
    count += 1
    print(count)
}

fn main() {
    bump(1)
}""")

        self.assertIn("static void bump(int count) {", c_code)
        self.assertIn("count = count + 1;", c_code)

    def test_plus_assignment_inside_loop(self):
        c_code = compile_source("""fn main() {
    let count = 0
    while count < 3 {
        count += 1
    }
}""")

        self.assertIn("while (count < 3) {", c_code)
        self.assertIn("count = count + 1;", c_code)

    def test_minus_assignment_subtracts_from_existing_int(self):
        c_code = compile_source("""fn main() {
    let count = 3
    count -= 1
    print(count)
}""")

        self.assertIn("int count = 3;", c_code)
        self.assertIn("count = count - 1;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_minus_assignment_can_use_int_expression(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    let count = 10
    count -= add(1, 2)
    count -= (5 - 2)
    print(count)
}""")

        self.assertIn("count = count - add(1, 2);", c_code)
        self.assertIn("count = count - (5 - 2);", c_code)

    def test_function_parameter_can_use_minus_assignment(self):
        c_code = compile_source("""fn lower(count: int) {
    count -= 1
    print(count)
}

fn main() {
    lower(3)
}""")

        self.assertIn("static void lower(int count) {", c_code)
        self.assertIn("count = count - 1;", c_code)

    def test_minus_assignment_inside_loop(self):
        c_code = compile_source("""fn main() {
    let count = 3
    while count > 0 {
        count -= 1
    }
}""")

        self.assertIn("while (count > 0) {", c_code)
        self.assertIn("count = count - 1;", c_code)

    def test_multiply_assignment_multiplies_existing_int(self):
        c_code = compile_source("""fn main() {
    let count = 3
    count *= 2
    print(count)
}""")

        self.assertIn("int count = 3;", c_code)
        self.assertIn("count = count * 2;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_multiply_assignment_can_use_int_expression(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    let count = 2
    count *= add(1, 2)
    count *= (2 + 3)
    print(count)
}""")

        self.assertIn("count = count * add(1, 2);", c_code)
        self.assertIn("count = count * (2 + 3);", c_code)

    def test_function_parameter_can_use_multiply_assignment(self):
        c_code = compile_source("""fn scale(count: int) {
    count *= 2
    print(count)
}

fn main() {
    scale(3)
}""")

        self.assertIn("static void scale(int count) {", c_code)
        self.assertIn("count = count * 2;", c_code)

    def test_multiply_assignment_inside_loop(self):
        c_code = compile_source("""fn main() {
    let count = 1
    while count < 8 {
        count *= 2
    }
}""")

        self.assertIn("while (count < 8) {", c_code)
        self.assertIn("count = count * 2;", c_code)

    def test_divide_assignment_divides_existing_int(self):
        c_code = compile_source("""fn main() {
    let count = 8
    count /= 2
    print(count)
}""")

        self.assertIn("int count = 8;", c_code)
        self.assertIn("count = count / 2;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_divide_assignment_can_use_int_expression(self):
        c_code = compile_source("""fn half(value: int) -> int {
    return value / 2
}

fn main() {
    let count = 24
    count /= half(8)
    count /= (6 / 2)
    print(count)
}""")

        self.assertIn("count = count / half(8);", c_code)
        self.assertIn("count = count / (6 / 2);", c_code)

    def test_function_parameter_can_use_divide_assignment(self):
        c_code = compile_source("""fn shrink(count: int) {
    count /= 2
    print(count)
}

fn main() {
    shrink(8)
}""")

        self.assertIn("static void shrink(int count) {", c_code)
        self.assertIn("count = count / 2;", c_code)

    def test_divide_assignment_inside_loop(self):
        c_code = compile_source("""fn main() {
    let count = 8
    while count > 1 {
        count /= 2
    }
}""")

        self.assertIn("while (count > 1) {", c_code)
        self.assertIn("count = count / 2;", c_code)

    def test_modulo_assignment_updates_existing_int(self):
        c_code = compile_source("""fn main() {
    let count = 7
    count %= 3
    print(count)
}""")

        self.assertIn("int count = 7;", c_code)
        self.assertIn("count = count % 3;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_modulo_assignment_can_use_int_expression(self):
        c_code = compile_source("""fn remainder(value: int) -> int {
    return value % 5
}

fn main() {
    let count = 29
    count %= remainder(12)
    count %= (10 % 4)
    print(count)
}""")

        self.assertIn("count = count % remainder(12);", c_code)
        self.assertIn("count = count % (10 % 4);", c_code)

    def test_function_parameter_can_use_modulo_assignment(self):
        c_code = compile_source("""fn shrink(count: int) {
    count %= 3
    print(count)
}

fn main() {
    shrink(8)
}""")

        self.assertIn("static void shrink(int count) {", c_code)
        self.assertIn("count = count % 3;", c_code)

    def test_modulo_assignment_inside_loop(self):
        c_code = compile_source("""fn main() {
    let count = 29
    while count > 5 {
        count %= 5
        break
    }
}""")

        self.assertIn("while (count > 5) {", c_code)
        self.assertIn("count = count % 5;", c_code)

    def test_break_and_continue_inside_while(self):
        c_code = compile_source("""fn main() {
    let count = 0
    while count < 5 {
        count = count + 1
        if count < 2 {
            continue
        }
        if count > 3 {
            break
        }
        print(count)
    }
}""")

        self.assertIn("while (count < 5) {", c_code)
        self.assertIn("continue;", c_code)
        self.assertIn("break;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_for_loop_counts_from_start_to_exclusive_end(self):
        c_code = compile_source("""fn main() {
    for i from 0 to 3 {
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i < 3; i = i + 1) {", c_code)
        self.assertIn('printf("%d\\n", i);', c_code)

    def test_for_loop_step_counts_by_custom_increment(self):
        c_code = compile_source("""fn main() {
    for i from 0 to 6 step 2 {
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i < 6; i = i + 2) {", c_code)
        self.assertIn('printf("%d\\n", i);', c_code)

    def test_for_loop_through_counts_to_inclusive_end(self):
        c_code = compile_source("""fn main() {
    for i from 0 through 3 {
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i <= 3; i = i + 1) {", c_code)
        self.assertIn('printf("%d\\n", i);', c_code)

    def test_for_loop_through_step_counts_by_custom_increment(self):
        c_code = compile_source("""fn main() {
    for i from 0 through 6 step 2 {
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i <= 6; i = i + 2) {", c_code)
        self.assertIn('printf("%d\\n", i);', c_code)

    def test_parenthesized_addition_prints_grouped_expression(self):
        c_code = compile_source("""fn main() {
    print((1 + 2))
}""")

        self.assertIn('printf("%d\\n", (1 + 2));', c_code)

    def test_parenthesized_addition_can_initialize_variable(self):
        c_code = compile_source("""fn main() {
    let count = (1 + 2)
    print(count)
}""")

        self.assertIn("int count = (1 + 2);", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_parenthesized_expression_can_be_compared(self):
        c_code = compile_source("""fn main() {
    let ok = (1 + 2) == 3
    if (ok) {
        print("ok")
    }
}""")

        self.assertIn("int ok = (1 + 2) == 3;", c_code)
        self.assertIn("if ((ok)) {", c_code)

    def test_parenthesized_expression_can_be_argument_and_return_value(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return (a + b)
}

fn show(value: int) {
    print(value)
}

fn main() {
    show((add(1, 2)))
}""")

        self.assertIn("return (a + b);", c_code)
        self.assertIn("show((add(1, 2)));", c_code)

    def test_for_loop_step_can_use_int_expression(self):
        c_code = compile_source("""fn step_size() -> int {
    return 2
}

fn main() {
    let amount = 1 + 1
    for i from 0 to 6 step step_size() {
        print(i)
    }
    for j from 0 to 6 step amount {
        print(j)
    }
}""")

        self.assertIn("for (int i = 0; i < 6; i = i + step_size()) {", c_code)
        self.assertIn("for (int j = 0; j < 6; j = j + amount) {", c_code)

    def test_for_loop_bounds_can_use_int_expressions(self):
        c_code = compile_source("""fn limit() -> int {
    return 4
}

fn main() {
    let start = 1
    for i from start to limit() {
        print(i)
    }
}""")

        self.assertIn("for (int i = start; i < limit(); i = i + 1) {", c_code)
        self.assertIn('printf("%d\\n", i);', c_code)

    def test_break_and_continue_inside_for(self):
        c_code = compile_source("""fn main() {
    for i from 0 to 5 {
        if i < 1 {
            continue
        }
        if i > 3 {
            break
        }
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i < 5; i = i + 1) {", c_code)
        self.assertIn("continue;", c_code)
        self.assertIn("break;", c_code)

    def test_break_and_continue_inside_for_step(self):
        c_code = compile_source("""fn main() {
    for i from 0 to 6 step 2 {
        if i < 2 {
            continue
        }
        if i > 4 {
            break
        }
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i < 6; i = i + 2) {", c_code)
        self.assertIn("continue;", c_code)
        self.assertIn("break;", c_code)

    def test_break_and_continue_inside_for_through(self):
        c_code = compile_source("""fn main() {
    for i from 0 through 5 {
        if i < 1 {
            continue
        }
        if i > 3 {
            break
        }
        print(i)
    }
}""")

        self.assertIn("for (int i = 0; i <= 5; i = i + 1) {", c_code)
        self.assertIn("continue;", c_code)
        self.assertIn("break;", c_code)

    def test_function_parameter_can_be_reassigned(self):
        c_code = compile_source("""fn bump(count: int) {
    count = count + 1
    print(count)
}

fn main() {
    bump(1)
}""")

        self.assertIn("static void bump(int count) {", c_code)
        self.assertIn("count = count + 1;", c_code)
        self.assertIn('printf("%d\\n", count);', c_code)

    def test_parse_source_builds_while_and_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 0
    while count < 3 {
        count = count + 1
    }
}""")

        while_stmt = program.statements[1]
        assign_stmt = while_stmt.statements[0]
        self.assertIsInstance(while_stmt, WhileStmt)
        self.assertEqual(
            while_stmt.condition,
            lai_compiler.CompareExpr(NameExpr("count"), "<", IntExpr(3)),
        )
        self.assertEqual(
            assign_stmt,
            AssignStmt("count", AddExpr([NameExpr("count"), IntExpr(1)]), 4),
        )

    def test_parse_source_builds_plus_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 0
    count += 1
}""")

        plus_assign = program.statements[1]
        self.assertEqual(type(plus_assign).__name__, "PlusAssignStmt")
        self.assertEqual(plus_assign.name, "count")
        self.assertEqual(plus_assign.value, IntExpr(1))
        self.assertEqual(plus_assign.line, 3)

    def test_parse_source_builds_minus_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 3
    count -= 1
}""")

        minus_assign = program.statements[1]
        self.assertEqual(minus_assign, MinusAssignStmt("count", IntExpr(1), 3))

    def test_parse_source_builds_multiply_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 3
    count *= 2
}""")

        multiply_assign = program.statements[1]
        self.assertEqual(multiply_assign, MultiplyAssignStmt("count", IntExpr(2), 3))

    def test_parse_source_builds_divide_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 8
    count /= 2
}""")

        divide_assign = program.statements[1]
        self.assertEqual(divide_assign, DivideAssignStmt("count", IntExpr(2), 3))

    def test_parse_source_builds_modulo_assignment_ast(self):
        program = parse_source("""fn main() {
    let count = 7
    count %= 3
}""")

        modulo_assign = program.statements[1]
        self.assertEqual(modulo_assign, ModuloAssignStmt("count", IntExpr(3), 3))

    def test_parse_source_builds_break_and_continue_ast(self):
        program = parse_source("""fn main() {
    let count = 0
    while count < 5 {
        if count < 2 {
            continue
        }
        break
    }
}""")

        while_stmt = program.statements[1]
        nested_if = while_stmt.statements[0]
        self.assertIsInstance(nested_if.statements[0], ContinueStmt)
        self.assertEqual(nested_if.statements[0], ContinueStmt(5))
        self.assertEqual(while_stmt.statements[1], BreakStmt(7))

    def test_parse_source_builds_for_loop_ast(self):
        program = parse_source("""fn main() {
    for i from 0 to 3 {
        print(i)
    }
}""")

        for_stmt = program.statements[0]
        self.assertIsInstance(for_stmt, ForStmt)
        self.assertEqual(
            for_stmt,
            ForStmt("i", IntExpr(0), IntExpr(3), [PrintStmt(NameExpr("i"), 3)], 2),
        )

    def test_parse_source_builds_for_step_ast(self):
        program = parse_source("""fn main() {
    for i from 0 to 6 step 2 {
        print(i)
    }
}""")

        for_stmt = program.statements[0]
        self.assertIsInstance(for_stmt, ForStmt)
        self.assertEqual(for_stmt.name, "i")
        self.assertEqual(for_stmt.start, IntExpr(0))
        self.assertEqual(for_stmt.end, IntExpr(6))
        self.assertEqual(for_stmt.step, IntExpr(2))
        self.assertEqual(for_stmt.statements, [PrintStmt(NameExpr("i"), 3)])
        self.assertEqual(for_stmt.line, 2)

    def test_parse_source_builds_for_through_ast(self):
        program = parse_source("""fn main() {
    for i from 0 through 3 {
        print(i)
    }
}""")

        for_stmt = program.statements[0]
        self.assertIsInstance(for_stmt, ForStmt)
        self.assertTrue(for_stmt.inclusive_end)
        self.assertEqual(for_stmt.name, "i")
        self.assertEqual(for_stmt.start, IntExpr(0))
        self.assertEqual(for_stmt.end, IntExpr(3))
        self.assertIsNone(for_stmt.step)
        self.assertEqual(for_stmt.statements, [PrintStmt(NameExpr("i"), 3)])
        self.assertEqual(for_stmt.line, 2)

    def test_parse_source_builds_group_expression_ast(self):
        program = parse_source("""fn main() {
    let count = (1 + 2)
}""")

        self.assertEqual(
            program.statements[0].value,
            GroupExpr(AddExpr([IntExpr(1), IntExpr(2)])),
        )

    def test_parse_source_builds_subtraction_expression_ast(self):
        program = parse_source("""fn main() {
    let count = 5 - 2
}""")

        self.assertEqual(
            program.statements[0].value,
            SubtractExpr(IntExpr(5), IntExpr(2)),
        )

    def test_parse_source_builds_multiplication_expression_ast(self):
        program = parse_source("""fn main() {
    let count = 2 * 3
}""")

        self.assertEqual(
            program.statements[0].value,
            MultiplyExpr([IntExpr(2), IntExpr(3)]),
        )

    def test_parse_source_builds_multiplication_precedence_ast(self):
        program = parse_source("""fn main() {
    let count = 2 + 3 * 4
}""")

        self.assertEqual(
            program.statements[0].value,
            AddExpr([IntExpr(2), MultiplyExpr([IntExpr(3), IntExpr(4)])]),
        )

    def test_parse_source_builds_division_expression_ast(self):
        program = parse_source("""fn main() {
    let count = 8 / 2
}""")

        self.assertEqual(
            program.statements[0].value,
            DivideExpr(IntExpr(8), IntExpr(2)),
        )

    def test_parse_source_builds_division_precedence_ast(self):
        program = parse_source("""fn main() {
    let count = 8 + 6 / 2
}""")

        self.assertEqual(
            program.statements[0].value,
            AddExpr([IntExpr(8), DivideExpr(IntExpr(6), IntExpr(2))]),
        )

    def test_parse_source_builds_modulo_expression_ast(self):
        program = parse_source("""fn main() {
    let count = 7 % 3
}""")

        self.assertEqual(
            program.statements[0].value,
            ModuloExpr(IntExpr(7), IntExpr(3)),
        )

    def test_parse_source_builds_modulo_precedence_ast(self):
        program = parse_source("""fn main() {
    let count = 8 + 7 % 3
}""")

        self.assertEqual(
            program.statements[0].value,
            AddExpr([IntExpr(8), ModuloExpr(IntExpr(7), IntExpr(3))]),
        )

    def test_rejects_incomplete_comparison(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(1 <)\n}")

    def test_rejects_unclosed_parenthesized_expression(self):
        with self.assertRaisesRegex(LaiCompileError, "expected RPAREN"):
            compile_source("fn main() {\n    print((1 + 2)\n}")

    def test_rejects_empty_parenthesized_expression(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(())\n}")

    def test_rejects_subtraction_with_non_int_operand(self):
        source = """fn main() {
    print(1 - "x")
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: subtraction operands must both be int, got int and string",
        ):
            compile_source(source)

    def test_rejects_incomplete_subtraction(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(1 -)\n}")

    def test_rejects_multiplication_with_non_int_operand(self):
        source = """fn main() {
    print(1 * "x")
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: multiplication operands must all be int, got string",
        ):
            compile_source(source)

    def test_rejects_division_with_non_int_operand(self):
        source = """fn main() {
    print(8 / "x")
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: division operands must both be int, got int and string",
        ):
            compile_source(source)

    def test_rejects_static_division_by_zero(self):
        source = """fn main() {
    print(8 / 0)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: division by zero"):
            compile_source(source)

    def test_rejects_grouped_static_division_by_zero(self):
        source = """fn main() {
    print(8 / (0))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: division by zero"):
            compile_source(source)

    def test_rejects_modulo_with_non_int_operand(self):
        source = """fn main() {
    print(7 % "x")
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: modulo operands must both be int, got int and string",
        ):
            compile_source(source)

    def test_rejects_static_modulo_by_zero(self):
        source = """fn main() {
    print(7 % 0)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: modulo by zero"):
            compile_source(source)

    def test_rejects_grouped_static_modulo_by_zero(self):
        source = """fn main() {
    print(7 % (0))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: modulo by zero"):
            compile_source(source)

    def test_rejects_modulo_assignment_to_unknown_variable(self):
        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: count"):
            compile_source("fn main() {\n    count %= 3\n}")

    def test_rejects_modulo_assignment_to_non_int_variable(self):
        source = """fn main() {
    let name = "JD"
    name %= 3
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot use %= with name of type string",
        ):
            compile_source(source)

    def test_rejects_modulo_assignment_with_non_int_value(self):
        source = """fn main() {
    let count = 7
    count %= true
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: %= value must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_modulo_assignment_by_static_zero(self):
        with self.assertRaisesRegex(LaiCompileError, "line 3: modulo by zero"):
            compile_source("fn main() {\n    let count = 7\n    count %= 0\n}")

    def test_rejects_modulo_assignment_by_grouped_static_zero(self):
        with self.assertRaisesRegex(LaiCompileError, "line 3: modulo by zero"):
            compile_source("fn main() {\n    let count = 7\n    count %= (0)\n}")

    def test_rejects_incomplete_multiplication(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(1 *)\n}")

    def test_rejects_incomplete_division(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(8 /)\n}")

    def test_rejects_incomplete_modulo(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(7 %)\n}")

    def test_parse_source_builds_recursive_unary_ast(self):
        program = parse_source(
            "fn main() {\n"
            "    print(-5)\n"
            "    print(+5)\n"
            "    print(--5)\n"
            "}"
        )

        self.assertEqual(program.statements[0].value, UnaryExpr("-", IntExpr(5)))
        self.assertEqual(program.statements[1].value, UnaryExpr("+", IntExpr(5)))
        self.assertEqual(
            program.statements[2].value,
            UnaryExpr("-", UnaryExpr("-", IntExpr(5))),
        )

    def test_unary_has_precedence_over_multiplication_and_addition(self):
        value = parse_source(
            "fn main() {\n    print(-2 * 3 + 4)\n}"
        ).statements[0].value

        self.assertEqual(
            value,
            AddExpr(
                [MultiplyExpr([UnaryExpr("-", IntExpr(2)), IntExpr(3)]), IntExpr(4)]
            ),
        )

    def test_multiplication_accepts_unary_right_operand(self):
        value = parse_source(
            "fn main() {\n    print(2 * -3)\n}"
        ).statements[0].value

        self.assertEqual(
            value,
            MultiplyExpr([IntExpr(2), UnaryExpr("-", IntExpr(3))]),
        )

    def test_rejects_incomplete_unary_expression(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            parse_source("fn main() {\n    print(-)\n}")

    def test_count_minus_minus_is_not_a_decrement_statement(self):
        with self.assertRaisesRegex(LaiCompileError, "expected LPAREN"):
            parse_source("fn main() {\n    let count = 1\n    count--\n}")

    def test_unary_integer_expressions_generate_parenthesized_c(self):
        generated = compile_source(
            "fn main() {\n"
            "    let count = 3\n"
            "    print(-5)\n"
            "    print(+count)\n"
            "    print(-count)\n"
            "    print(-(2 + 3))\n"
            "    print(2 * -3)\n"
            "    print(--5)\n"
            "}"
        )

        self.assertIn('printf("%d\\n", (-(5)));', generated)
        self.assertIn('printf("%d\\n", (+(count)));', generated)
        self.assertIn('printf("%d\\n", (-(count)));', generated)
        self.assertIn('printf("%d\\n", (-((2 + 3))));', generated)
        self.assertIn('printf("%d\\n", 2 * (-(3)));', generated)
        self.assertIn('printf("%d\\n", (-((-(5)))));', generated)

    def test_accepts_i32_min_unary_literal(self):
        generated = compile_source(
            "fn main() {\n    print(-2147483648)\n    print(-(2147483648))\n}"
        )
        self.assertEqual(generated.count("(-2147483647 - 1)"), 2)

    def test_rejects_integer_literals_outside_i32_range(self):
        sources = ["2147483648", "+2147483648", "-+2147483648", "-2147483649"]
        for expression in sources:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(
                    LaiCompileError,
                    "integer literal out of i32 range",
                ):
                    compile_source(f"fn main() {{\n    print({expression})\n}}")

    def test_rejects_static_i32_min_negation_overflow(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: integer unary negation overflow",
        ):
            compile_source("fn main() {\n    print(-(-2147483648))\n}")

    def test_unary_static_zero_is_rejected_for_division_and_modulo(self):
        cases = [("8 / -0", "division by zero"), ("8 % +0", "modulo by zero")]
        for expression, message in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LaiCompileError, message):
                    compile_source(f"fn main() {{\n    print({expression})\n}}")

    def test_rejects_statically_non_positive_for_steps(self):
        steps = ["-1", "-(1 + 1)", "1 - 2", "-0", "1 - 1"]
        for step in steps:
            with self.subTest(step=step):
                with self.assertRaisesRegex(
                    LaiCompileError,
                    "line 2: for step must be greater than 0",
                ):
                    compile_source(
                        f"fn main() {{\n    for i from 0 to 3 step {step} {{\n"
                        "        print(i)\n    }\n}"
                    )

    def test_negative_for_bounds_remain_valid(self):
        generated = compile_source(
            "fn main() {\n    for i from -2 to 2 {\n        print(i)\n    }\n}"
        )
        self.assertIn("for (int i = (-(2)); i < 2; i = i + 1)", generated)

    def test_rejects_unary_minus_for_string(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: unary - operand must be int, got string",
        ):
            compile_source('fn main() {\n    print(-"LAI")\n}')

    def test_rejects_unary_plus_for_bool(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            r"line 2: unary \+ operand must be int, got bool",
        ):
            compile_source("fn main() {\n    print(+true)\n}")

    def test_rejects_unary_operator_on_void_call(self):
        source = "fn greet() {\n}\n\nfn main() {\n    print(-greet())\n}"
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 5: function greet does not return a value",
        ):
            compile_source(source)

    def test_unary_is_accepted_in_existing_integer_expression_positions(self):
        source = """fn negate(value: int) -> int {
    return -value
}

fn main() {
    let count = -3
    count = -count
    count += -1
    count -= -1
    count *= -2
    count /= -1
    count %= -2
    print(negate(-count))
    if -1 < +count {
        print(-count)
    }
    for i from -2 to +2 {
        print(-i)
    }
}"""

        generated = compile_source(source)
        self.assertIn("return (-(value));", generated)
        self.assertIn("count = (-(count));", generated)
        self.assertIn("negate((-(count)))", generated)
        self.assertIn("for (int i = (-(2)); i < (+(2));", generated)

    def test_checker_rejects_unknown_unary_operator_ast(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: unsupported unary operator: !",
        ):
            generate_c(Program([PrintStmt(UnaryExpr("!", IntExpr(1)), 1)]))

    def test_c_checked_entry_rejects_unknown_unary_operator_ast(self):
        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: unsupported unary operator: !",
        ):
            C_BACKEND.emit(Program([PrintStmt(UnaryExpr("!", IntExpr(1)), 1)]))

    def test_ordering_comparisons_reject_non_integer_types(self):
        operand_pairs = [
            ('"A"', '"B"', "string", "string"),
            ("true", "false", "bool", "bool"),
            ('"A"', "1", "string", "int"),
            ("1", '"A"', "int", "string"),
            ("true", "1", "bool", "int"),
            ("1", "false", "int", "bool"),
        ]

        for operator in ("<", "<=", ">", ">="):
            for left, right, left_kind, right_kind in operand_pairs:
                with self.subTest(operator=operator, left=left, right=right):
                    message = (
                        "line 2: ordering comparison operands must both be int, "
                        f"got {left_kind} and {right_kind}"
                    )
                    with self.assertRaisesRegex(LaiCompileError, message):
                        compile_source(
                            f"fn main() {{\n    print({left} {operator} {right})\n}}"
                        )

    def test_equality_comparisons_reject_mixed_types(self):
        operands = [("1", "int"), ("true", "bool"), ('"LAI"', "string")]

        for operator in ("==", "!="):
            for left, left_kind in operands:
                for right, right_kind in operands:
                    if left_kind == right_kind:
                        continue
                    with self.subTest(operator=operator, left=left, right=right):
                        message = (
                            "line 2: equality comparison operands must have the same type, "
                            f"got {left_kind} and {right_kind}"
                        )
                        with self.assertRaisesRegex(LaiCompileError, message):
                            compile_source(
                                f"fn main() {{\n    print({left} {operator} {right})\n}}"
                            )

    def test_checker_rejects_unknown_comparison_operator_ast(self):
        program = Program(
            [PrintStmt(CompareExpr(IntExpr(1), "<>", IntExpr(2)), 1)]
        )

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 1: unsupported comparison operator: <>",
        ):
            generate_c(program)

    def test_c_checked_entry_rejects_invalid_comparisons(self):
        cases = [
            (
                CompareExpr(IntExpr(1), "<>", IntExpr(2)),
                "line 1: unsupported comparison operator: <>",
            ),
            (
                CompareExpr(StringExpr("A"), "<", StringExpr("B")),
                "line 1: ordering comparison operands must both be int, "
                "got string and string",
            ),
            (
                CompareExpr(BoolExpr(True), ">=", BoolExpr(False)),
                "line 1: ordering comparison operands must both be int, "
                "got bool and bool",
            ),
            (
                CompareExpr(StringExpr("A"), "==", IntExpr(1)),
                "line 1: equality comparison operands must have the same type, "
                "got string and int",
            ),
        ]

        for expression, message in cases:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LaiCompileError, message):
                    C_BACKEND.emit(Program([PrintStmt(expression, 1)]))

    def test_type_checker_reports_string_comparison(self):
        source = """fn main() {
    let name = "JD"
    let ok = name == 3
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: equality comparison operands must have the same type, "
            "got string and int",
        ):
            compile_source(source)

    def test_type_checker_reports_non_bool_if_condition(self):
        source = """fn main() {
    if 1 {
        print("bad")
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: if condition must be bool, got int",
        ):
            compile_source(source)

    def test_parenthesized_non_bool_if_condition_still_rejected(self):
        source = """fn main() {
    if (1 + 2) {
        print("bad")
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: if condition must be bool, got int",
        ):
            compile_source(source)

    def test_type_checker_reports_non_bool_while_condition(self):
        source = """fn main() {
    while 1 {
        print("bad")
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: while condition must be bool, got int",
        ):
            compile_source(source)

    def test_type_checker_reports_non_int_for_start(self):
        source = """fn main() {
    for i from true to 3 {
        print(i)
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: for start must be int, got bool",
        ):
            compile_source(source)

    def test_type_checker_reports_non_int_for_end(self):
        source = """fn main() {
    for i from 0 to false {
        print(i)
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: for end must be int, got bool",
        ):
            compile_source(source)

    def test_type_checker_reports_non_int_for_through_end(self):
        source = """fn main() {
    for i from 0 through false {
        print(i)
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: for end must be int, got bool",
        ):
            compile_source(source)

    def test_type_checker_reports_non_int_for_step(self):
        source = """fn main() {
    for i from 0 to 6 step true {
        print(i)
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: for step must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_zero_for_step(self):
        source = """fn main() {
    for i from 0 to 6 step 0 {
        print(i)
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: for step must be greater than 0",
        ):
            compile_source(source)

    def test_step_keyword_is_not_a_variable_name(self):
        source = """fn main() {
    let step = 1
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2.*invalid variable name"):
            compile_source(source)

    def test_through_keyword_is_not_a_variable_name(self):
        source = """fn main() {
    let through = 1
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2.*invalid variable name"):
            compile_source(source)

    def test_rejects_assignment_to_unknown_variable(self):
        source = """fn main() {
    missing = 1
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: missing"):
            compile_source(source)

    def test_rejects_assignment_type_mismatch(self):
        source = """fn main() {
    let count = 1
    count = "bad"
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot assign string to count of type int",
        ):
            compile_source(source)

    def test_rejects_plus_assignment_to_unknown_variable(self):
        source = """fn main() {
    missing += 1
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: missing"):
            compile_source(source)

    def test_rejects_plus_assignment_to_non_int_variable(self):
        source = """fn main() {
    let name = "JD"
    name += 1
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot use \\+= with name of type string",
        ):
            compile_source(source)

    def test_rejects_plus_assignment_with_non_int_value(self):
        source = """fn main() {
    let count = 1
    count += true
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: \\+= value must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_minus_assignment_to_unknown_variable(self):
        source = """fn main() {
    missing -= 1
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: missing"):
            compile_source(source)

    def test_rejects_minus_assignment_to_non_int_variable(self):
        source = """fn main() {
    let name = "JD"
    name -= 1
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot use -= with name of type string",
        ):
            compile_source(source)

    def test_rejects_minus_assignment_with_non_int_value(self):
        source = """fn main() {
    let count = 1
    count -= true
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: -= value must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_multiply_assignment_to_unknown_variable(self):
        source = """fn main() {
    missing *= 2
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: missing"):
            compile_source(source)

    def test_rejects_multiply_assignment_to_non_int_variable(self):
        source = """fn main() {
    let name = "JD"
    name *= 2
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot use \\*= with name of type string",
        ):
            compile_source(source)

    def test_rejects_multiply_assignment_with_non_int_value(self):
        source = """fn main() {
    let count = 3
    count *= true
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: \\*= value must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_divide_assignment_to_unknown_variable(self):
        source = """fn main() {
    missing /= 2
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: unknown variable: missing"):
            compile_source(source)

    def test_rejects_divide_assignment_to_non_int_variable(self):
        source = """fn main() {
    let name = "JD"
    name /= 2
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: cannot use /= with name of type string",
        ):
            compile_source(source)

    def test_rejects_divide_assignment_with_non_int_value(self):
        source = """fn main() {
    let count = 8
    count /= true
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: /= value must be int, got bool",
        ):
            compile_source(source)

    def test_rejects_divide_assignment_by_static_zero(self):
        source = """fn main() {
    let count = 8
    count /= 0
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 3: division by zero"):
            compile_source(source)

    def test_rejects_divide_assignment_by_grouped_static_zero(self):
        source = """fn main() {
    let count = 8
    count /= (0)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 3: division by zero"):
            compile_source(source)

    def test_while_body_variables_do_not_leak(self):
        source = """fn main() {
    let count = 0
    while count < 1 {
        let hidden = 1
        count = count + 1
    }
    print(hidden)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 7: unknown variable: hidden"):
            compile_source(source)

    def test_for_loop_variable_does_not_leak(self):
        source = """fn main() {
    for i from 0 to 3 {
        print(i)
    }
    print(i)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 5: unknown variable: i"):
            compile_source(source)

    def test_for_loop_body_variables_do_not_leak(self):
        source = """fn main() {
    for i from 0 to 3 {
        let hidden = i
    }
    print(hidden)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 5: unknown variable: hidden"):
            compile_source(source)

    def test_rejects_for_loop_variable_shadowing_existing_variable(self):
        source = """fn main() {
    let i = 10
    for i from 0 to 3 {
        print(i)
    }
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 3: variable already defined: i"):
            compile_source(source)

    def test_rejects_return_in_while_inside_void_function(self):
        source = """fn greet(ready: bool) {
    while ready {
        return "bad"
    }
}

fn main() {
    greet(true)
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: return is only allowed in functions with return type",
        ):
            compile_source(source)

    def test_rejects_while_as_only_returning_function_exit(self):
        source = """fn value(ready: bool) -> int {
    while ready {
        print("waiting")
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_returning_function_allows_return_inside_while_before_final_return(self):
        c_code = compile_source("""fn find(limit: int) -> int {
    let count = 0
    while count < limit {
        if count > 2 {
            return count
        }
        count = count + 1
    }
    return limit
}

fn main() {
    print(find(5))
}""")

        self.assertIn("while (count < limit) {", c_code)
        self.assertIn("return count;", c_code)
        self.assertIn("return limit;", c_code)
        self.assertIn('printf("%d\\n", find(5));', c_code)

    def test_rejects_wrong_loop_return_type(self):
        source = """fn find(limit: int) -> int {
    let count = 0
    while count < limit {
        return "bad"
    }
    return limit
}

fn main() {
    print(find(5))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 4: return type must be int, got string"):
            compile_source(source)

    def test_rejects_loop_return_before_later_statement_in_same_block(self):
        source = """fn find(limit: int) -> int {
    let count = 0
    while count < limit {
        return count
        count = count + 1
    }
    return limit
}

fn main() {
    print(find(5))
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 4: return must be the final statement in its block",
        ):
            compile_source(source)

    def test_rejects_final_while_with_return_as_guaranteed_exit(self):
        source = """fn value() -> int {
    while true {
        return 1
    }
}

fn main() {
    print(value())
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_returning_function_allows_return_inside_for_before_final_return(self):
        c_code = compile_source("""fn find(limit: int) -> int {
    for i from 0 to limit {
        if i > 2 {
            return i
        }
    }
    return limit
}

fn main() {
    print(find(5))
}""")

        self.assertIn("for (int i = 0; i < limit; i = i + 1) {", c_code)
        self.assertIn("return i;", c_code)
        self.assertIn("return limit;", c_code)

    def test_returning_function_allows_return_inside_for_step_before_final_return(self):
        c_code = compile_source("""fn find(limit: int) -> int {
    for i from 0 to limit step 2 {
        if i > 2 {
            return i
        }
    }
    return limit
}

fn main() {
    print(find(5))
}""")

        self.assertIn("for (int i = 0; i < limit; i = i + 2) {", c_code)
        self.assertIn("return i;", c_code)
        self.assertIn("return limit;", c_code)

    def test_returning_function_allows_return_inside_for_through_before_final_return(self):
        c_code = compile_source("""fn find(limit: int) -> int {
    for i from 0 through limit {
        if i > 2 {
            return i
        }
    }
    return limit
}

fn main() {
    print(find(5))
}""")

        self.assertIn("for (int i = 0; i <= limit; i = i + 1) {", c_code)
        self.assertIn("return i;", c_code)
        self.assertIn("return limit;", c_code)

    def test_rejects_final_for_with_return_as_guaranteed_exit(self):
        source = """fn value() -> int {
    for i from 0 to 3 {
        return i
    }
}

fn main() {
    print(value())
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_rejects_break_outside_loop(self):
        source = """fn main() {
    break
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: break is only allowed inside loop",
        ):
            compile_source(source)

    def test_rejects_continue_outside_loop(self):
        source = """fn main() {
    continue
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: continue is only allowed inside loop",
        ):
            compile_source(source)

    def test_rejects_break_in_if_outside_loop(self):
        source = """fn main() {
    if true {
        break
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: break is only allowed inside loop",
        ):
            compile_source(source)

    def test_else_branch_does_not_see_then_branch_variables(self):
        source = """fn main() {
    if true {
        let hidden = 1
    } else {
        print(hidden)
    }
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 5: unknown variable: hidden"):
            compile_source(source)

    def test_type_checker_reports_non_bool_else_if_condition(self):
        source = """fn main() {
    if true {
        print("ok")
    } else if 1 {
        print("bad")
    }
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 4: if condition must be bool, got int",
        ):
            compile_source(source)

    def test_parse_source_builds_if_else_ast(self):
        program = parse_source("""fn main() {
    if true {
        print("yes")
    } else {
        print("no")
    }
}""")

        self.assertEqual(
            program.statements[0],
            IfStmt(
                BoolExpr(True),
                [PrintStmt(StringExpr("yes"), 3)],
                2,
                [PrintStmt(StringExpr("no"), 5)],
            ),
        )

    def test_user_defined_function_call(self):
        c_code = compile_source("""fn greet() {
    print("Hello from function")
}

fn main() {
    greet()
}""")

        self.assertIn("static void greet(void);", c_code)
        self.assertIn("static void greet(void) {", c_code)
        self.assertIn('printf("Hello from function\\n");', c_code)
        self.assertIn("int main(void) {", c_code)
        self.assertIn("    greet();", c_code)

    def test_user_defined_function_with_string_parameter(self):
        c_code = compile_source("""fn greet(name: string) {
    print(name)
}

fn main() {
    greet("JD")
}""")

        self.assertIn("static void greet(const char* name);", c_code)
        self.assertIn("static void greet(const char* name) {", c_code)
        self.assertIn('printf("%s\\n", name);', c_code)
        self.assertIn('    greet("JD");', c_code)

    def test_user_defined_function_with_multiple_parameters(self):
        c_code = compile_source("""fn show(name: string, count: int, ready: bool) {
    print(name)
    print(count)
    print(ready)
}

fn main() {
    show("JD", 3, true)
}""")

        self.assertIn("static void show(const char* name, int count, int ready);", c_code)
        self.assertIn("static void show(const char* name, int count, int ready) {", c_code)
        self.assertIn('printf("%s\\n", name);', c_code)
        self.assertIn('printf("%d\\n", count);', c_code)
        self.assertIn('printf("%d\\n", ready);', c_code)
        self.assertIn('    show("JD", 3, 1);', c_code)

    def test_function_parameter_can_be_used_in_if(self):
        c_code = compile_source("""fn check(ready: bool) {
    if ready {
        print("ready")
    }
}

fn main() {
    check(true)
}""")

        self.assertIn("static void check(int ready) {", c_code)
        self.assertIn("if (ready) {", c_code)
        self.assertIn("    check(1);", c_code)

    def test_parse_source_builds_function_parameters_and_call_args(self):
        program = parse_source("""fn greet(name: string, count: int) {
    print(name)
}

fn main() {
    greet("JD", 3)
}""")

        function = program.functions[0]
        call = program.statements[0]
        self.assertEqual(function.params[0].name, "name")
        self.assertEqual(function.params[0].type_name, "string")
        self.assertEqual(function.params[1].name, "count")
        self.assertEqual(function.params[1].type_name, "int")
        self.assertEqual(call.args[0], StringExpr("JD"))
        self.assertEqual(call.args[1], IntExpr(3))

    def test_user_defined_function_with_int_return_value(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    let count = add(1, 2)
    print(count)
    print(add(3, 4))
}""")

        self.assertIn("static int add(int a, int b);", c_code)
        self.assertIn("static int add(int a, int b) {", c_code)
        self.assertIn("return a + b;", c_code)
        self.assertIn("int count = add(1, 2);", c_code)
        self.assertIn('printf("%d\\n", add(3, 4));', c_code)

    def test_user_defined_function_with_string_and_bool_return_values(self):
        c_code = compile_source("""fn label() -> string {
    return "ready"
}

fn is_ready(count: int) -> bool {
    return count == 3
}

fn main() {
    let count = 3
    print(label())
    print(is_ready(count))
    if is_ready(count) {
        print("ok")
    }
}""")

        self.assertIn("static const char* label(void);", c_code)
        self.assertIn("static int is_ready(int count);", c_code)
        self.assertIn('return "ready";', c_code)
        self.assertIn("return count == 3;", c_code)
        self.assertIn('printf("%s\\n", label());', c_code)
        self.assertIn('printf("%d\\n", is_ready(count));', c_code)
        self.assertIn("if (is_ready(count)) {", c_code)

    def test_function_call_expression_can_be_passed_as_argument_and_returned(self):
        c_code = compile_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn twice(value: int) -> int {
    return add(value, value)
}

fn main() {
    print(twice(add(1, 2)))
}""")

        self.assertIn("return add(value, value);", c_code)
        self.assertIn('printf("%d\\n", twice(add(1, 2)));', c_code)

    def test_returning_function_can_return_from_if_else(self):
        c_code = compile_source("""fn grade(score: int) -> string {
    if score > 90 {
        return "A"
    } else {
        return "B"
    }
}

fn main() {
    print(grade(95))
}""")

        self.assertIn("static const char* grade(int score);", c_code)
        self.assertIn("if (score > 90) {", c_code)
        self.assertIn('return "A";', c_code)
        self.assertIn('return "B";', c_code)
        self.assertIn('printf("%s\\n", grade(95));', c_code)

    def test_returning_function_can_return_from_else_if_chain(self):
        c_code = compile_source("""fn grade(score: int) -> string {
    if score > 90 {
        return "A"
    } else if score > 80 {
        return "B"
    } else {
        return "C"
    }
}

fn main() {
    print(grade(85))
}""")

        self.assertIn("if (score > 90) {", c_code)
        self.assertIn("if (score > 80) {", c_code)
        self.assertIn('return "A";', c_code)
        self.assertIn('return "B";', c_code)
        self.assertIn('return "C";', c_code)

    def test_returning_function_allows_statements_before_branch_return(self):
        c_code = compile_source("""fn pick(ready: bool) -> int {
    if ready {
        let value = 1
        return value
    } else {
        print("fallback")
        return 2
    }
}

fn main() {
    print(pick(true))
}""")

        self.assertIn("int value = 1;", c_code)
        self.assertIn("return value;", c_code)
        self.assertIn('printf("fallback\\n");', c_code)
        self.assertIn("return 2;", c_code)

    def test_returning_function_accepts_nested_final_if_returns(self):
        c_code = compile_source("""fn choose(first: bool, second: bool) -> int {
    if first {
        if second {
            return 1
        } else {
            return 2
        }
    } else {
        return 3
    }
}

fn main() {
    print(choose(true, false))
}""")

        self.assertIn("if (first) {", c_code)
        self.assertIn("if (second) {", c_code)
        self.assertIn("return 1;", c_code)
        self.assertIn("return 2;", c_code)
        self.assertIn("return 3;", c_code)

    def test_returning_function_branch_symbols_do_not_leak_between_branches(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        let hidden = 1
        return hidden
    } else {
        return hidden
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 6: unknown variable: hidden"):
            compile_source(source)

    def test_parse_source_builds_return_type_return_stmt_and_call_expr(self):
        program = parse_source("""fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    let count = add(1, 2)
}""")

        function = program.functions[0]
        return_stmt = function.statements[0]
        let_stmt = program.statements[0]
        self.assertEqual(function.return_type, "int")
        self.assertIsInstance(return_stmt, ReturnStmt)
        self.assertEqual(
            return_stmt.value,
            AddExpr([NameExpr("a"), NameExpr("b")]),
        )
        self.assertEqual(
            let_stmt.value,
            CallExpr("add", [IntExpr(1), IntExpr(2)], 6),
        )

    def test_rejects_invalid_return_type(self):
        source = """fn value() -> number {
    return 1
}

fn main() {
    print(value())
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: invalid return type: number"):
            compile_source(source)

    def test_rejects_missing_final_return(self):
        source = """fn value() -> int {
    let count = 1
}

fn main() {
    print(value())
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_rejects_wrong_return_type(self):
        source = """fn value() -> int {
    return "bad"
}

fn main() {
    print(value())
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: return type must be int, got string"):
            compile_source(source)

    def test_rejects_return_in_void_function(self):
        source = """fn greet() {
    return "bad"
}

fn main() {
    greet()
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: return is only allowed in functions with return type",
        ):
            compile_source(source)

    def test_rejects_return_before_final_top_level_statement(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
    }
    return 2
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: return must be the final statement in its block",
        ):
            compile_source(source)

    def test_rejects_branch_return_without_else(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_rejects_branch_return_when_one_path_does_not_return(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
    } else {
        print("missing")
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: function value must end with return"):
            compile_source(source)

    def test_rejects_wrong_branch_return_type(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return "bad"
    } else {
        return 1
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 3: return type must be int, got string"):
            compile_source(source)

    def test_rejects_return_before_final_statement_in_branch(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
        print("after")
    } else {
        return 2
    }
}

fn main() {
    print(value(true))
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: return must be the final statement in its block",
        ):
            compile_source(source)

    def test_rejects_branch_return_in_void_function(self):
        source = """fn greet(ready: bool) {
    if ready {
        return "bad"
    }
}

fn main() {
    greet(true)
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: return is only allowed in functions with return type",
        ):
            compile_source(source)

    def test_rejects_void_function_call_as_expression(self):
        source = """fn greet() {
    print("hi")
}

fn main() {
    let value = greet()
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 6: function greet does not return a value",
        ):
            compile_source(source)

    def test_rejects_wrong_call_expression_argument_count(self):
        source = """fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    print(add(1))
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 6: function add expects 2 arguments, got 1",
        ):
            compile_source(source)

    def test_rejects_wrong_call_expression_argument_type(self):
        source = """fn add(a: int, b: int) -> int {
    return a + b
}

fn main() {
    print(add("x", 2))
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 6: argument 1 for add must be int, got string",
        ):
            compile_source(source)

    def test_rejects_main_function_return_type(self):
        source = """fn main() -> int {
    return 0
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: main function cannot have return type"):
            compile_source(source)

    def test_rejects_return_in_main_function(self):
        source = """fn main() {
    return 0
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 2: return is only allowed in functions with return type",
        ):
            compile_source(source)

    def test_rejects_wrong_function_argument_count(self):
        source = """fn greet(name: string) {
    print(name)
}

fn main() {
    greet()
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 6: function greet expects 1 arguments, got 0",
        ):
            compile_source(source)

    def test_rejects_wrong_function_argument_type(self):
        source = """fn greet(name: string) {
    print(name)
}

fn main() {
    greet(123)
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 6: argument 1 for greet must be string, got int",
        ):
            compile_source(source)

    def test_rejects_duplicate_parameter_name(self):
        source = """fn show(name: string, name: int) {
    print(name)
}

fn main() {
    show("JD", 3)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: parameter already defined: name"):
            compile_source(source)

    def test_rejects_invalid_parameter_type(self):
        source = """fn greet(name: number) {
    print(name)
}

fn main() {
    greet(1)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: invalid parameter type: number"):
            compile_source(source)

    def test_rejects_let_shadowing_function_parameter(self):
        source = """fn greet(name: string) {
    let name = "shadow"
    print(name)
}

fn main() {
    greet("JD")
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 2: variable already defined: name"):
            compile_source(source)

    def test_rejects_main_function_parameters(self):
        source = """fn main(name: string) {
    print(name)
}"""

        with self.assertRaisesRegex(LaiCompileError, "line 1: main function cannot have parameters"):
            compile_source(source)

    def test_user_function_can_call_another_user_function(self):
        c_code = compile_source("""fn greet() {
    print("hi")
}

fn wrapper() {
    greet()
}

fn main() {
    wrapper()
}""")

        self.assertIn("static void greet(void);", c_code)
        self.assertIn("static void wrapper(void);", c_code)
        self.assertIn("    greet();", c_code)
        self.assertIn("    wrapper();", c_code)

    def test_rejects_duplicate_function_name(self):
        source = """fn greet() {
    print("one")
}

fn greet() {
    print("two")
}

fn main() {
    greet()
}"""

        with self.assertRaisesRegex(LaiCompileError, "function already defined"):
            compile_source(source)

    def test_rejects_unknown_function_call(self):
        source = """fn main() {
    missing()
}"""

        with self.assertRaisesRegex(LaiCompileError, "unknown function: missing"):
            compile_source(source)


if __name__ == "__main__":
    unittest.main()
