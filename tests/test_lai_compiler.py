import unittest

from lai_compiler import (
    IntExpr,
    LaiCompileError,
    LetStmt,
    NameExpr,
    PrintStmt,
    Program,
    StringExpr,
    Token,
    compile_source,
    generate_c,
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
}'''

        c_code = compile_source(source)

        self.assertIn('printf("B\\n");', c_code)
        self.assertIn('const char* name = "J";', c_code)


if __name__ == "__main__":
    unittest.main()
