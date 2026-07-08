import contextlib
import io
import unittest

import lai_compiler
from lai_compiler import (
    AddExpr,
    BoolExpr,
    CallExpr,
    IfStmt,
    IntExpr,
    LaiCompileError,
    LetStmt,
    NameExpr,
    PrintStmt,
    Program,
    ReturnStmt,
    StringExpr,
    Token,
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

    def test_tokenize_return_type_and_return_statement(self):
        source = """fn add(a: int) -> int {
    return a
}"""

        tokens = tokenize(source)

        self.assertIn(Token("ARROW", "->", 1, 16), tokens)
        self.assertIn(Token("RETURN", "return", 2, 5), tokens)

    def test_cli_help_uses_ly_source_extension(self):
        output = io.StringIO()

        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(output):
                compiler_main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("Compile LAI v0.13 source", help_text)
        self.assertIn(".ly source file", help_text)
        self.assertNotIn(".lai source file", help_text)

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

    def test_rejects_incomplete_comparison(self):
        with self.assertRaisesRegex(LaiCompileError, "expected expression"):
            compile_source("fn main() {\n    print(1 <)\n}")

    def test_type_checker_reports_string_comparison(self):
        source = """fn main() {
    let name = "JD"
    let ok = name == 3
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            "line 3: comparison operands must both be int, got string and int",
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
            "line 3: return must be the final top-level statement",
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
