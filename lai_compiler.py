import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from lai_ast import (
    AddExpr,
    AssignStmt,
    BoolExpr,
    BreakStmt,
    CallExpr,
    CallStmt,
    CompareExpr,
    ContinueStmt,
    DivideAssignStmt,
    DivideExpr,
    Expr,
    ForStmt,
    FunctionDef,
    GroupExpr,
    IfStmt,
    IntExpr,
    LetStmt,
    MinusAssignStmt,
    ModuloAssignStmt,
    ModuloExpr,
    MultiplyAssignStmt,
    MultiplyExpr,
    NameExpr,
    Param,
    PlusAssignStmt,
    PrintStmt,
    Program,
    ReturnStmt,
    Stmt,
    StringExpr,
    SubtractExpr,
    UnaryExpr,
    WhileStmt,
)
from lai_core import LaiCompileError
from lai_checker import check_program
from lai_backend import Backend
from lai_c_backend import C_BACKEND, generate_c
from lai_llvm_backend import LLVM_BACKEND


_BACKENDS = {
    "c": C_BACKEND,
    "llvm": LLVM_BACKEND,
}


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KEYWORDS = {
    "fn": "FN",
    "main": "MAIN",
    "let": "LET",
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "return": "RETURN",
    "while": "WHILE",
    "for": "FOR",
    "from": "FROM",
    "to": "TO",
    "step": "STEP",
    "through": "THROUGH",
    "break": "BREAK",
    "continue": "CONTINUE",
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
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "<": "LT",
    ">": "GT",
    ":": "COLON",
    ",": "COMMA",
}
_DOUBLE_CHAR_TOKENS = {
    "==": "EQUAL_EQUAL",
    "!=": "BANG_EQUAL",
    "<=": "LT_EQUAL",
    ">=": "GT_EQUAL",
    "->": "ARROW",
    "+=": "PLUS_EQUAL",
    "-=": "MINUS_EQUAL",
    "*=": "STAR_EQUAL",
    "/=": "SLASH_EQUAL",
    "%=": "PERCENT_EQUAL",
}
_COMPARISON_TOKEN_KINDS = frozenset(
    {"LT", "LT_EQUAL", "GT", "GT_EQUAL", "EQUAL_EQUAL", "BANG_EQUAL"}
)


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

        pair = source[index : index + 2]
        if pair in _DOUBLE_CHAR_TOKENS:
            tokens.append(Token(_DOUBLE_CHAR_TOKENS[pair], pair, line, column))
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
                if function.params:
                    raise LaiCompileError(
                        f"line {function.line}: main function cannot have parameters"
                    )
                if function.return_type:
                    raise LaiCompileError(
                        f"line {function.line}: main function cannot have return type"
                    )
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
        params = self._parse_parameters()
        self._consume("RPAREN")
        return_type = None
        if self._match("ARROW"):
            return_type = self._consume("IDENT").value
        self._consume("LBRACE")
        statements = self._parse_block_body()
        return FunctionDef(name.value, statements, name.line, params or None, return_type)

    def _parse_parameters(self) -> list[Param]:
        params: list[Param] = []
        if self._check("RPAREN"):
            return params

        while True:
            if not self._check_name_token():
                token = self._peek()
                raise LaiCompileError(
                    f"line {token.line}, column {token.column}: invalid parameter name"
                )
            name = self._advance()
            self._consume("COLON")
            type_token = self._consume("IDENT")
            params.append(Param(name.value, type_token.value, name.line))

            if not self._match("COMMA"):
                break

        return params

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
        if self._check_assignment_start():
            name = self._advance()
            self._consume("EQUAL")
            value = self._parse_literal_expr()
            return AssignStmt(name.value, value, name.line)

        if self._check_plus_assignment_start():
            name = self._advance()
            self._consume("PLUS_EQUAL")
            value = self._parse_expr(allow_string=False, allow_name=True)
            return PlusAssignStmt(name.value, value, name.line)

        if self._check_minus_assignment_start():
            name = self._advance()
            self._consume("MINUS_EQUAL")
            value = self._parse_expr(allow_string=False, allow_name=True)
            return MinusAssignStmt(name.value, value, name.line)

        if self._check_multiply_assignment_start():
            name = self._advance()
            self._consume("STAR_EQUAL")
            value = self._parse_expr(allow_string=False, allow_name=True)
            return MultiplyAssignStmt(name.value, value, name.line)

        if self._check_divide_assignment_start():
            name = self._advance()
            self._consume("SLASH_EQUAL")
            value = self._parse_expr(allow_string=False, allow_name=True)
            return DivideAssignStmt(name.value, value, name.line)

        if self._check_modulo_assignment_start():
            name = self._advance()
            self._consume("PERCENT_EQUAL")
            value = self._parse_expr(allow_string=False, allow_name=True)
            return ModuloAssignStmt(name.value, value, name.line)

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
            return self._parse_if_statement(self._previous())

        if self._match("WHILE"):
            return self._parse_while_statement(self._previous())

        if self._match("FOR"):
            return self._parse_for_statement(self._previous())

        if self._match("BREAK"):
            return BreakStmt(self._previous().line)

        if self._match("CONTINUE"):
            return ContinueStmt(self._previous().line)

        if self._match("RETURN"):
            return_token = self._previous()
            return ReturnStmt(
                self._parse_expr(allow_string=True, allow_name=True),
                return_token.line,
            )

        if self._match("IDENT"):
            name = self._previous()
            self._consume("LPAREN")
            args = self._parse_call_args()
            self._consume("RPAREN")
            return CallStmt(name.value, name.line, args or None)

        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: unsupported statement")

    def _parse_if_statement(self, if_token: Token) -> IfStmt:
        condition = self._parse_expr(allow_string=True, allow_name=True)
        self._consume("LBRACE")
        statements = self._parse_block_body()
        return IfStmt(condition, statements, if_token.line, self._parse_optional_else_body())

    def _parse_while_statement(self, while_token: Token) -> WhileStmt:
        condition = self._parse_expr(allow_string=True, allow_name=True)
        self._consume("LBRACE")
        statements = self._parse_block_body()
        return WhileStmt(condition, statements, while_token.line)

    def _parse_for_statement(self, for_token: Token) -> ForStmt:
        if not self._check_name_token():
            token = self._peek()
            raise LaiCompileError(
                f"line {token.line}, column {token.column}: invalid for variable name"
            )
        name = self._advance()
        self._consume("FROM")
        start = self._parse_expr(allow_string=False, allow_name=True)
        inclusive_end = False
        if self._match("TO"):
            inclusive_end = False
        elif self._match("THROUGH"):
            inclusive_end = True
        else:
            self._consume("TO")
        end = self._parse_expr(allow_string=False, allow_name=True)
        step = None
        if self._match("STEP"):
            step = self._parse_expr(allow_string=False, allow_name=True)
        self._consume("LBRACE")
        statements = self._parse_block_body()
        return ForStmt(name.value, start, end, statements, for_token.line, step, inclusive_end)

    def _parse_optional_else_body(self) -> list[Stmt] | None:
        if not self._match_else_clause():
            return None

        if self._match("IF"):
            # else if 是语法糖：AST 里表示成 else 分支包含一个嵌套 IfStmt。
            return [self._parse_if_statement(self._previous())]

        self._consume("LBRACE")
        return self._parse_block_body()

    def _parse_call_args(self) -> list[Expr]:
        args: list[Expr] = []
        if self._check("RPAREN"):
            return args

        while True:
            args.append(self._parse_expr(allow_string=True, allow_name=True))
            if not self._match("COMMA"):
                break

        return args

    def _parse_literal_expr(self) -> Expr:
        return self._parse_expr(allow_string=True, allow_name=True)

    def _parse_print_expr(self) -> Expr:
        return self._parse_expr(allow_string=True, allow_name=True)

    def _parse_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        left = self._parse_add_expr(allow_string, allow_name)
        if self._peek().kind in _COMPARISON_TOKEN_KINDS:
            operator = self._advance().value
            right = self._parse_add_expr(allow_string, allow_name)
            if self._peek().kind in _COMPARISON_TOKEN_KINDS:
                token = self._peek()
                raise LaiCompileError(
                    f"line {token.line}, column {token.column}: "
                    "comparison chains are not supported"
                )
            return CompareExpr(left, operator, right)
        return left

    def _parse_add_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        expr = self._parse_multiply_expr(allow_string, allow_name)

        while self._match("PLUS") or self._match("MINUS"):
            operator = self._previous().kind
            right = self._parse_multiply_expr(allow_string, allow_name)
            if operator == "PLUS":
                if isinstance(expr, AddExpr):
                    expr = AddExpr([*expr.terms, right])
                else:
                    expr = AddExpr([expr, right])
            else:
                expr = SubtractExpr(expr, right)

        return expr

    def _parse_multiply_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        expr = self._parse_unary_expr(allow_string, allow_name)

        while self._match("STAR") or self._match("SLASH") or self._match("PERCENT"):
            operator = self._previous().kind
            right = self._parse_unary_expr(allow_string, allow_name)
            if operator == "STAR":
                if isinstance(expr, MultiplyExpr):
                    expr = MultiplyExpr([*expr.factors, right])
                else:
                    expr = MultiplyExpr([expr, right])
            elif operator == "SLASH":
                expr = DivideExpr(expr, right)
            else:
                expr = ModuloExpr(expr, right)

        return expr

    def _parse_unary_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        if self._match("PLUS") or self._match("MINUS"):
            operator = self._previous().value
            return UnaryExpr(operator, self._parse_unary_expr(allow_string, allow_name))
        return self._parse_primary_expr(allow_string, allow_name)

    def _parse_primary_expr(self, allow_string: bool, allow_name: bool) -> Expr:
        if allow_string and self._match("STRING"):
            return StringExpr(self._previous().value)
        if self._match("TRUE"):
            return BoolExpr(True)
        if self._match("FALSE"):
            return BoolExpr(False)
        if self._match("INT"):
            return IntExpr(int(self._previous().value))
        if self._match("LPAREN"):
            value = self._parse_expr(allow_string=allow_string, allow_name=allow_name)
            self._consume("RPAREN")
            return GroupExpr(value)
        if allow_name and self._match("IDENT"):
            name = self._previous()
            if self._match("LPAREN"):
                args = self._parse_call_args()
                self._consume("RPAREN")
                return CallExpr(name.value, args or None, name.line)
            return NameExpr(name.value)
        if allow_name and self._check_keyword_name():
            return NameExpr(self._advance().value)
        token = self._peek()
        raise LaiCompileError(f"line {token.line}, column {token.column}: expected expression")

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

    def _match_else_clause(self) -> bool:
        checkpoint = self.current

        if self._match("ELSE"):
            return True

        # 允许 C 风格的换行写法：右花括号下一行再写 else。
        while self._check("NEWLINE"):
            self._advance()

        if self._match("ELSE"):
            return True

        self.current = checkpoint
        return False

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _check_name_token(self) -> bool:
        return self._check("IDENT") or self._check_keyword_name()

    def _check_keyword_name(self) -> bool:
        return self._peek().kind in {"FN", "MAIN", "LET", "PRINT"}

    def _check_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "EQUAL"

    def _check_plus_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "PLUS_EQUAL"

    def _check_minus_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "MINUS_EQUAL"

    def _check_multiply_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "STAR_EQUAL"

    def _check_divide_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "SLASH_EQUAL"

    def _check_modulo_assignment_start(self) -> bool:
        return self._check_name_token() and self._peek_next().kind == "PERCENT_EQUAL"

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().kind == "EOF"

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peek_next(self) -> Token:
        if self.current + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.current + 1]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]


def parse_source(source: str) -> Program:
    return Parser(tokenize(source)).parse_program()


def compile_source(source: str, backend: Backend = C_BACKEND) -> str:
    program = parse_source(source)
    check_program(program)
    return backend.emit(program)


def compile_file(
    source_path: Path,
    build_dir: Path,
    backend: Backend = C_BACKEND,
) -> tuple[Path, Path]:
    source = source_path.read_text(encoding="utf-8")
    generated_source = compile_source(source, backend)

    build_dir.mkdir(parents=True, exist_ok=True)
    generated_path = build_dir / f"{source_path.stem}{backend.source_suffix}"
    exe_path = build_dir / f"{source_path.stem}.exe"
    generated_path.write_text(generated_source, encoding="utf-8")

    backend.build(generated_path, exe_path)
    return generated_path, exe_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile LAI v0.35 source with C or experimental LLVM backend."
    )
    parser.add_argument("source", type=Path, help="Path to a .ly source file.")
    parser.add_argument(
        "--backend",
        choices=tuple(_BACKENDS),
        default="c",
        help="Code generation backend (default: c).",
    )
    parser.add_argument("--run", action="store_true", help="Run the executable after compiling.")
    args = parser.parse_args(argv)

    source_path = args.source
    build_dir = source_path.parent / "build"
    backend = _BACKENDS[args.backend]

    try:
        generated_path, exe_path = compile_file(source_path, build_dir, backend)
        print(f"Wrote {generated_path}", flush=True)
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
