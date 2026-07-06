import argparse
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


class Stmt:
    pass


@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class PrintStmt(Stmt):
    value: "Expr"
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
class NameExpr(Expr):
    name: str


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KEYWORDS = {
    "fn": "FN",
    "main": "MAIN",
    "let": "LET",
    "print": "PRINT",
}
_SINGLE_CHAR_TOKENS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "=": "EQUAL",
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
    index += 1
    column += 1
    value_chars: list[str] = []

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
            escape = source[index + 1]
            escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
            if escape not in escapes:
                raise LaiCompileError(f"line {line}, column {column}: unsupported escape sequence")
            value_chars.append(escapes[escape])
            index += 2
            column += 2
            continue
        value_chars.append(char)
        index += 1
        column += 1

    if index >= len(source):
        raise LaiCompileError(
            f"line {start_line}, column {start_column}: unterminated string literal"
        )

    index += 1
    column += 1
    return Token("STRING", "".join(value_chars), start_line, start_column), index, column


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse_program(self) -> Program:
        self._skip_newlines()
        self._consume("FN")
        self._consume("MAIN")
        self._consume("LPAREN")
        self._consume("RPAREN")
        self._consume("LBRACE")
        self._consume_newline_or_before("RBRACE")

        statements: list[Stmt] = []
        while not self._check("RBRACE"):
            self._skip_newlines()
            if self._check("RBRACE"):
                break
            statements.append(self._parse_statement())
            self._consume_newline_or_before("RBRACE")

        self._consume("RBRACE")
        self._skip_newlines()
        self._consume("EOF")
        return Program(statements)

    def _parse_statement(self) -> Stmt:
        if self._match("LET"):
            if not self._check("IDENT"):
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

        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: unsupported statement")

    def _parse_literal_expr(self) -> Expr:
        if self._match("STRING"):
            return StringExpr(self._previous().value)
        if self._match("INT"):
            return IntExpr(int(self._previous().value))
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected literal")

    def _parse_print_expr(self) -> Expr:
        if self._match("STRING"):
            return StringExpr(self._previous().value)
        if self._match("IDENT"):
            return NameExpr(self._previous().value)
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected print argument")

    def _consume(self, kind: str) -> Token:
        if self._check(kind):
            return self._advance()
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected {kind}")

    def _consume_newline_or_before(self, kind: str) -> None:
        if self._check(kind):
            return
        self._consume("NEWLINE")
        self._skip_newlines()

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
    symbols: dict[str, str] = {}
    c_lines = ["#include <stdio.h>", "", "int main(void) {"]

    for statement in program.statements:
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
                c_lines.append(f"    const char* {statement.name} = {c_value};")
            elif value_kind == "int":
                c_lines.append(f"    int {statement.name} = {c_value};")
            continue

        if isinstance(statement, PrintStmt):
            c_lines.append(_print_stmt_to_c(statement, symbols))
            continue

        raise LaiCompileError("internal error: unsupported statement node")

    c_lines.append("    return 0;")
    c_lines.append("}")
    c_lines.append("")
    return "\n".join(c_lines)


def _expr_to_c_value(expr: Expr, symbols: dict[str, str], line: int) -> tuple[str, str]:
    if isinstance(expr, StringExpr):
        return "string", _escape_c_string(expr.value)
    if isinstance(expr, IntExpr):
        return "int", str(expr.value)
    if isinstance(expr, NameExpr):
        if expr.name not in symbols:
            raise LaiCompileError(f"line {line}: unknown variable: {expr.name}")
        return symbols[expr.name], expr.name
    raise LaiCompileError("internal error: unsupported expression node")


def _print_stmt_to_c(statement: PrintStmt, symbols: dict[str, str]) -> str:
    if isinstance(statement.value, StringExpr):
        return f"    printf({_escape_c_string(statement.value.value + chr(10))});"

    if isinstance(statement.value, NameExpr):
        if statement.value.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.value.name}")
        value_kind = symbols[statement.value.name]
        if value_kind == "string":
            return f'    printf("%s\\n", {statement.value.name});'
        if value_kind == "int":
            return f'    printf("%d\\n", {statement.value.name});'

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
