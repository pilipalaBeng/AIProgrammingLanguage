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
_LET_RE = re.compile(r"^let\s+(.+?)\s*=\s*(.+)$")
_PRINT_RE = re.compile(r"^print\((.*)\)$")
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
            name = self._consume("IDENT")
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


def compile_source(source: str) -> str:
    lines = source.splitlines()
    non_empty = [(index + 1, line.strip()) for index, line in enumerate(lines) if line.strip()]

    if not non_empty or non_empty[0][1] != "fn main() {":
        raise LaiCompileError("line 1: expected 'fn main() {'")

    closing_line, closing_text = non_empty[-1]
    if closing_text != "}":
        raise LaiCompileError(f"line {closing_line}: expected '}}'")

    symbols = {}
    c_lines = ["#include <stdio.h>", "", "int main(void) {"]

    start_index = non_empty[0][0]
    end_index = closing_line
    for line_number, raw_line in enumerate(lines[start_index:end_index - 1], start_index + 1):
        statement = raw_line.strip()
        if not statement:
            continue

        c_lines.append(_compile_statement(statement, line_number, symbols))

    c_lines.append("    return 0;")
    c_lines.append("}")
    c_lines.append("")
    return "\n".join(c_lines)


def compile_file(source_path: Path, build_dir: Path) -> tuple[Path, Path]:
    source = source_path.read_text(encoding="utf-8")
    c_code = compile_source(source)

    build_dir.mkdir(parents=True, exist_ok=True)
    c_path = build_dir / f"{source_path.stem}.c"
    exe_path = build_dir / f"{source_path.stem}.exe"
    c_path.write_text(c_code, encoding="utf-8")

    _run_clang(c_path, exe_path)
    return c_path, exe_path


def _compile_statement(statement: str, line_number: int, symbols: dict[str, str]) -> str:
    let_match = _LET_RE.match(statement)
    if let_match:
        name, value_text = let_match.groups()
        if not _NAME_RE.match(name):
            raise LaiCompileError(f"line {line_number}: invalid variable name: {name}")
        if name in symbols:
            raise LaiCompileError(f"line {line_number}: variable already defined: {name}")

        value_kind, c_value = _compile_value(value_text.strip(), line_number)
        symbols[name] = value_kind
        if value_kind == "string":
            return f"    const char* {name} = {c_value};"
        if value_kind == "int":
            return f"    int {name} = {c_value};"

    print_match = _PRINT_RE.match(statement)
    if print_match:
        argument = print_match.group(1).strip()
        if _is_string_literal(argument):
            c_literal = _string_to_c_literal(argument, line_number, suffix="\n")
            return f"    printf({c_literal});"

        if not _NAME_RE.match(argument):
            raise LaiCompileError(f"line {line_number}: invalid print argument")
        if argument not in symbols:
            raise LaiCompileError(f"line {line_number}: unknown variable: {argument}")
        if symbols[argument] == "string":
            return f'    printf("%s\\n", {argument});'
        if symbols[argument] == "int":
            return f'    printf("%d\\n", {argument});'

    raise LaiCompileError(f"line {line_number}: unsupported syntax: {statement}")


def _compile_value(value_text: str, line_number: int) -> tuple[str, str]:
    if _is_string_literal(value_text):
        return "string", _string_to_c_literal(value_text, line_number)
    if re.fullmatch(r"[0-9]+", value_text):
        return "int", value_text
    raise LaiCompileError(f"line {line_number}: unsupported let value: {value_text}")


def _is_string_literal(text: str) -> bool:
    return len(text) >= 2 and text[0] == '"' and text[-1] == '"'


def _string_to_c_literal(text: str, line_number: int, suffix: str = "") -> str:
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise LaiCompileError(f"line {line_number}: invalid string literal") from exc

    if not isinstance(value, str):
        raise LaiCompileError(f"line {line_number}: invalid string literal")
    return _escape_c_string(value + suffix)


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
