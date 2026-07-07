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

    def test_if_statement(self):
        c_code = compile_source("""fn main() {
    if 1 < 2 {
        print("yes")
    }
}""")

        self.assertIn("if (1 < 2) {", c_code)
        self.assertIn('printf("yes\\n");', c_code)

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

    def test_rejects_incomplete_comparison(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(1 <)\n}")

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
