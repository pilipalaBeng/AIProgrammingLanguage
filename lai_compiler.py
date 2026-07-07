import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class LaiCompileError(Exception):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class Program:
    statements: list["Stmt"]
    functions: list["FunctionDef"] | None = None


class Stmt:
    pass


@dataclass(frozen=True)
class FunctionDef:
    name: str
    statements: list["Stmt"]
    line: int


@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class PrintStmt(Stmt):
    value: "Expr"
    line: int


@dataclass(frozen=True)
class IfStmt(Stmt):
    condition: "Expr"
    statements: list["Stmt"]
    line: int


@dataclass(frozen=True)
class CallStmt(Stmt):
    name: str
    line: int


class Expr:
    pass


@dataclass(frozen=True)
class StringExpr(Expr):
    value: str


@dataclass(frozen=True)
class IntExpr(Expr):
    value: int


@dataclass(frozen=True)
class AddExpr(Expr):
    terms: list["Expr"]


@dataclass(frozen=True)
class BoolExpr(Expr):
    value: bool


@dataclass(frozen=True)
class CompareExpr(Expr):
    left: "Expr"
    operator: str
    right: "Expr"


@dataclass(frozen=True)
class NameExpr(Expr):
    name: str


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KEYWORDS = {
    "fn": "FN",
    "main": "MAIN",
    "let": "LET",
    "print": "PRINT",
    "if": "IF",
    "true": "TRUE",
    "false": "FALSE",
}
_SINGLE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "=": "EQUAL",
    "+": "PLUS",
    "<": "LT",
    ">": "GT",
}


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0
    line = 1
    column = 1

    while index < len(source):
        char = source[index]

        if char in " \t":
            index += 1
            column += 1
            continue

        if char == "\r":
            index += 1
            continue

        if char == "\n":
            tokens.append(Token("NEWLINE", "\n", line, column))
            index += 1
            line += 1
            column = 1
            continue

        if char == "/" and index + 1 < len(source) and source[index + 1] == "/":
            while index < len(source) and source[index] not in "\r\n":
                index += 1
                column += 1
            continue

        if char == "=" and index + 1 < len(source) and source[index + 1] == "=":
            tokens.append(Token("EQUAL_EQUAL", "==", line, column))
            index += 2
            column += 2
            continue

        if char in _SINGLE_CHAR_TOKENS:
            tokens.append(Token(_SINGLE_CHAR_TOKENS[char], char, line, column))
            index += 1
            column += 1
            continue

        if char == '"':
            string_token, index, column = _read_string(source, index, line, column)
            tokens.append(string_token)
            continue

        if char.isalpha() or char == "_":
            start = index
            start_column = column
            while index < len(source) and (source[index].isalnum() or source[index] == "_"):
                index += 1
                column += 1
            value = source[start:index]
            tokens.append(Token(_KEYWORDS.get(value, "IDENT"), value, line, start_column))
            continue

        if char.isdigit():
            start = index
            start_column = column
            while index < len(source) and source[index].isdigit():
                index += 1
                column += 1
            tokens.append(Token("INT", source[start:index], line, start_column))
            continue

        raise LaiCompileError(f"line {line}, column {column}: unexpected character: {char}")

    tokens.append(Token("EOF", "", line, column))
    return tokens


def _read_string(source: str, index: int, line: int, column: int) -> tuple[Token, int, int]:
    start_line = line
    start_column = column
    start_index = index
    index += 1
    column += 1

    while index < len(source) and source[index] != '"':
        char = source[index]
        if char == "\n":
            raise LaiCompileError(
                f"line {start_line}, column {start_column}: unterminated string literal"
            )
        if char == "\\":
            if index + 1 >= len(source):
                raise LaiCompileError(
                    f"line {start_line}, column {start_column}: unterminated string literal"
                )
            index += 2
            column += 2
            continue
        index += 1
        column += 1

    if index >= len(source):
        raise LaiCompileError(
            f"line {start_line}, column {start_column}: unterminated string literal"
        )

    index += 1
    column += 1
    literal_text = source[start_index:index]
    try:
        value = ast.literal_eval(literal_text)
    except (SyntaxError, ValueError) as exc:
        raise LaiCompileError(
            f"line {start_line}, column {start_column}: invalid string literal"
        ) from exc

    if not isinstance(value, str):
        raise LaiCompileError(f"line {start_line}, column {start_column}: invalid string literal")
    return Token("STRING", value, start_line, start_column), index, column


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse_program(self) -> Program:
        self._skip_newlines()

        functions: list[FunctionDef] = []
        main_function: FunctionDef | None = None
        seen_names: set[str] = set()

        while not self._check("EOF"):
            function = self._parse_function()
            if function.name in seen_names:
                raise LaiCompileError(f"line {function.line}: function already defined: {function.name}")
            seen_names.add(function.name)

            if function.name == "main":
                main_function = function
            else:
                functions.append(function)
            self._skip_newlines()

        if main_function is None:
            token = self._peek()
            raise LaiCompileError(f"line {token.line}, column {token.column}: expected main function")

        self._consume("EOF")
        return Program(main_function.statements, functions or None)

    def _parse_function(self) -> FunctionDef:
        self._consume("FN")
        if self._match("MAIN"):
            name = self._previous()
        else:
            name = self._consume("IDENT")
        self._consume("LPAREN")
        self._consume("RPAREN")
        self._consume("LBRACE")
        statements = self._parse_block_body()
        return FunctionDef(name.value, statements, name.line)

    def _parse_block_body(self) -> list[Stmt]:
        self._consume("NEWLINE")
        self._skip_newlines()

        statements: list[Stmt] = []
        while not self._check("RBRACE"):
            self._skip_newlines()
            if self._check("RBRACE"):
                break
            statements.append(self._parse_statement())
            self._consume("NEWLINE")
            self._skip_newlines()

        self._consume("RBRACE")
        return statements

    def _parse_statement(self) -> Stmt:
        if self._match("LET"):
            if not self._check_name_token():
                token = self._peek()
                raise LaiCompileError(
                    f"line {token.line}, column {token.column}: invalid variable name"
                )
            name = self._advance()
            self._consume("EQUAL")
            value = self._parse_literal_expr()
            return LetStmt(name.value, value, name.line)

        if self._match("PRINT"):
            print_token = self._previous()
            self._consume("LPAREN")
            value = self._parse_print_expr()
            self._consume("RPAREN")
            return PrintStmt(value, print_token.line)

        if self._match("IF"):
            if_token = self._previous()
            condition = self._parse_expr(allow_string=False, allow_name=True)
            self._consume("LBRACE")
            statements = self._parse_block_body()
            return IfStmt(condition, statements, if_token.line)

        if self._match("IDENT"):
            name = self._previous()
            self._consume("LPAREN")
            self._consume("RPAREN")
            return CallStmt(name.value, name.line)

        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: unsupported statement")

    def _parse_literal_expr(self) -> Expr:
        return self._parse_expr(allow_string=True, allow_name=True)

    def _parse_print_expr(self) -> Expr:
        return self._parse_expr(allow_string=True, allow_name=True)

    def _parse_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        left = self._parse_primary_expr(allow_string, allow_name)
        if self._match("LT") or self._match("GT") or self._match("EQUAL_EQUAL"):
            operator = self._previous().value
            right = self._parse_primary_expr(False, True)
            return CompareExpr(left, operator, right)
        return left

    def _parse_primary_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        if allow_string and self._match("STRING"):
            return StringExpr(self._previous().value)
        if self._match("TRUE"):
            return BoolExpr(True)
        if self._match("FALSE"):
            return BoolExpr(False)
        if self._check("INT"):
            return self._parse_int_expr()
        if allow_name and self._match("IDENT"):
            return NameExpr(self._previous().value)
        if allow_name and self._check_keyword_name():
            return NameExpr(self._advance().value)
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected expression")

    def _parse_int_expr(self) -> Expr:
        first = self._consume("INT")
        terms: list[Expr] = [IntExpr(int(first.value))]

        while self._match("PLUS"):
            if not self._check("INT"):
                token = self._peek()
                raise LaiCompileError(
                    f"line {token.line}, column {token.column}: expected integer after +"
                )
            term = self._advance()
            terms.append(IntExpr(int(term.value)))

        if len(terms) == 1:
            return terms[0]
        return AddExpr(terms)

    def _consume(self, kind: str) -> Token:
        if self._check(kind):
            return self._advance()
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected {kind}")

    def _skip_newlines(self) -> None:
        while self._check("NEWLINE"):
            self._advance()

    def _match(self, kind: str) -> bool:
        if not self._check(kind):
            return False
        self._advance()
        return True

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _check_name_token(self) -> bool:
        return self._check("IDENT") or self._check_keyword_name()

    def _check_keyword_name(self) -> bool:
        return self._peek().kind in {"FN", "MAIN", "LET", "PRINT"}

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().kind == "EOF"

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]


def parse_source(source: str) -> Program:
    return Parser(tokenize(source)).parse_program()


def generate_c(program: Program) -> str:
    functions = program.functions or []
    function_names = _collect_function_names(functions)
    c_lines = ["#include <stdio.h>", ""]

    for function in functions:
        c_lines.append(f"static void {function.name}(void);")

    if functions:
        c_lines.append("")

    for function in functions:
        c_lines.extend(_function_to_c(function, function_names))
        c_lines.append("")

    symbols: dict[str, str] = {}
    c_lines.append("int main(void) {")

    for statement in program.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_names))

    c_lines.append("    return 0;")
    c_lines.append("}")
    c_lines.append("")
    return "\n".join(c_lines)


def _collect_function_names(functions: list[FunctionDef]) -> set[str]:
    names: set[str] = set()
    for function in functions:
        if not _NAME_RE.match(function.name):
            raise LaiCompileError(f"line {function.line}: invalid function name: {function.name}")
        if function.name in names:
            raise LaiCompileError(f"line {function.line}: function already defined: {function.name}")
        names.add(function.name)
    return names


def _function_to_c(function: FunctionDef, function_names: set[str]) -> list[str]:
    symbols: dict[str, str] = {}
    c_lines = [f"static void {function.name}(void) {{"]
    for statement in function.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_names))
    c_lines.append("}")
    return c_lines


def _stmt_to_c(
    statement: Stmt,
    symbols: dict[str, str],
    indent_level: int,
    function_names: set[str] | None = None,
) -> list[str]:
    indent = "    " * indent_level

    if isinstance(statement, LetStmt):
        if not _NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name in symbols:
            raise LaiCompileError(
                f"line {statement.line}: variable already defined: {statement.name}"
            )

        value_kind, c_value = _expr_to_c_value(statement.value, symbols, statement.line)
        symbols[statement.name] = value_kind
        if value_kind == "string":
            return [f"{indent}const char* {statement.name} = {c_value};"]
        if value_kind in {"int", "bool"}:
            return [f"{indent}int {statement.name} = {c_value};"]
        raise LaiCompileError(f"line {statement.line}: invalid let value")

    if isinstance(statement, PrintStmt):
        return [_print_stmt_to_c(statement, symbols, indent)]

    if isinstance(statement, CallStmt):
        return [_call_stmt_to_c(statement, function_names or set(), indent)]

    if isinstance(statement, IfStmt):
        value_kind, c_condition = _expr_to_c_value(statement.condition, symbols, statement.line)
        if value_kind != "bool":
            raise LaiCompileError(f"line {statement.line}: if condition must be bool")
        block_symbols = symbols.copy()
        c_lines = [f"{indent}if ({c_condition}) {{"]
        for inner in statement.statements:
            c_lines.extend(_stmt_to_c(inner, block_symbols, indent_level + 1, function_names))
        c_lines.append(f"{indent}}}")
        return c_lines

    raise LaiCompileError("internal error: unsupported statement node")


def _call_stmt_to_c(statement: CallStmt, function_names: set[str], indent: str) -> str:
    if statement.name not in function_names:
        raise LaiCompileError(f"line {statement.line}: unknown function: {statement.name}")
    return f"{indent}{statement.name}();"


def _expr_to_c_value(expr: Expr, symbols: dict[str, str], line: int) -> tuple[str, str]:
    if isinstance(expr, StringExpr):
        return "string", _escape_c_string(expr.value)
    if isinstance(expr, IntExpr):
        return "int", str(expr.value)
    if isinstance(expr, BoolExpr):
        return "bool", "1" if expr.value else "0"
    if isinstance(expr, AddExpr):
        c_terms: list[str] = []
        for term in expr.terms:
            value_kind, c_value = _expr_to_c_value(term, symbols, line)
            if value_kind != "int":
                raise LaiCompileError(f"line {line}: invalid integer expression")
            c_terms.append(c_value)
        return "int", " + ".join(c_terms)
    if isinstance(expr, CompareExpr):
        left_kind, c_left = _expr_to_c_value(expr.left, symbols, line)
        right_kind, c_right = _expr_to_c_value(expr.right, symbols, line)
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(f"line {line}: comparison operands must be int")
        return "bool", f"{c_left} {expr.operator} {c_right}"
    if isinstance(expr, NameExpr):
        if expr.name not in symbols:
            raise LaiCompileError(f"line {line}: unknown variable: {expr.name}")
        return symbols[expr.name], expr.name
    raise LaiCompileError("internal error: unsupported expression node")


def _print_stmt_to_c(statement: PrintStmt, symbols: dict[str, str], indent: str = "    ") -> str:
    if isinstance(statement.value, StringExpr):
        return f"{indent}printf({_escape_c_string(statement.value.value + chr(10))});"

    if isinstance(statement.value, (IntExpr, AddExpr, BoolExpr, CompareExpr)):
        value_kind, c_value = _expr_to_c_value(statement.value, symbols, statement.line)
        if value_kind in {"int", "bool"}:
            return f'{indent}printf("%d\\n", {c_value});'

    if isinstance(statement.value, NameExpr):
        if statement.value.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.value.name}")
        value_kind = symbols[statement.value.name]
        if value_kind == "string":
            return f'{indent}printf("%s\\n", {statement.value.name});'
        if value_kind in {"int", "bool"}:
            return f'{indent}printf("%d\\n", {statement.value.name});'

    raise LaiCompileError(f"line {statement.line}: invalid print argument")


def compile_source(source: str) -> str:
    return generate_c(parse_source(source))


def compile_file(source_path: Path, build_dir: Path) -> tuple[Path, Path]:
    source = source_path.read_text(encoding="utf-8")
    c_code = compile_source(source)

    build_dir.mkdir(parents=True, exist_ok=True)
    c_path = build_dir / f"{source_path.stem}.c"
    exe_path = build_dir / f"{source_path.stem}.exe"
    c_path.write_text(c_code, encoding="utf-8")

    _run_clang(c_path, exe_path)
    return c_path, exe_path


def _escape_c_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _run_clang(c_path: Path, exe_path: Path) -> None:
    command = ["clang", str(c_path), "-o", str(exe_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise LaiCompileError(
            "failed to run clang: clang was not found. "
            "Open the x64 Native Tools Command Prompt for VS, or add clang to Path."
        ) from exc

    if result.returncode != 0:
        details = [
            "clang failed.",
            f"Command: {' '.join(command)}",
            "Tip: run this from the x64 Native Tools Command Prompt for VS.",
        ]
        if result.stdout.strip():
            details.append(f"stdout:\n{result.stdout.rstrip()}")
        if result.stderr.strip():
            details.append(f"stderr:\n{result.stderr.rstrip()}")
        raise LaiCompileError("\n".join(details))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile LAI v0 source to C and native exe.")
    parser.add_argument("source", type=Path, help="Path to a .lai source file.")
    parser.add_argument("--run", action="store_true", help="Run the executable after compiling.")
    args = parser.parse_args(argv)

    source_path = args.source
    build_dir = source_path.parent / "build"

    try:
        c_path, exe_path = compile_file(source_path, build_dir)
        print(f"Wrote {c_path}", flush=True)
        print(f"Built {exe_path}", flush=True)
        if args.run:
            result = subprocess.run([str(exe_path)], check=False)
            return result.returncode
        return 0
    except OSError as exc:
        print(f"LAI compile error: {exc}", file=sys.stderr)
        return 1
    except LaiCompileError as exc:
        print(f"LAI compile error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
