from lai_ast import (
    AddExpr,
    BoolExpr,
    CallStmt,
    CompareExpr,
    IfStmt,
    IntExpr,
    LetStmt,
    NameExpr,
    PrintStmt,
    StringExpr,
)
from lai_checker import check_program, collect_function_names
from lai_core import LaiCompileError, NAME_RE
from lai_stdlib import c_preamble, c_print_string_literal, c_print_value, escape_c_string


# C backend 只负责把检查过的 AST 输出成可读 C 代码。
def generate_c(program) -> str:
    check_program(program)
    functions = program.functions or []
    function_names = collect_function_names(functions)
    c_lines = [*c_preamble(), ""]

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


def _function_to_c(function, function_names: set[str]) -> list[str]:
    symbols: dict[str, str] = {}
    c_lines = [f"static void {function.name}(void) {{"]
    for statement in function.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_names))
    c_lines.append("}")
    return c_lines


def _stmt_to_c(
    statement,
    symbols: dict[str, str],
    indent_level: int,
    function_names: set[str] | None = None,
) -> list[str]:
    indent = "    " * indent_level

    if isinstance(statement, LetStmt):
        if not NAME_RE.match(statement.name):
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
        c_lines = [f"{indent}if ({c_condition}) {{"]
        then_symbols = symbols.copy()
        for inner in statement.statements:
            c_lines.extend(_stmt_to_c(inner, then_symbols, indent_level + 1, function_names))

        if statement.else_statements is not None:
            # else 分支也独立复制符号表，和 checker 的作用域规则保持一致。
            else_symbols = symbols.copy()
            c_lines.append(f"{indent}}} else {{")
            for inner in statement.else_statements:
                c_lines.extend(_stmt_to_c(inner, else_symbols, indent_level + 1, function_names))

        c_lines.append(f"{indent}}}")
        return c_lines

    raise LaiCompileError("internal error: unsupported statement node")


def _call_stmt_to_c(statement, function_names: set[str], indent: str) -> str:
    if statement.name not in function_names:
        raise LaiCompileError(f"line {statement.line}: unknown function: {statement.name}")
    return f"{indent}{statement.name}();"


def _expr_to_c_value(expr, symbols: dict[str, str], line: int) -> tuple[str, str]:
    if isinstance(expr, StringExpr):
        return "string", escape_c_string(expr.value)
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


def _print_stmt_to_c(statement, symbols: dict[str, str], indent: str = "    ") -> str:
    if isinstance(statement.value, StringExpr):
        return c_print_string_literal(statement.value.value, indent)

    if isinstance(statement.value, (IntExpr, AddExpr, BoolExpr, CompareExpr)):
        expr_kind, c_value = _expr_to_c_value(statement.value, symbols, statement.line)
        if expr_kind in {"int", "bool"}:
            return c_print_value(expr_kind, c_value, indent)

    if isinstance(statement.value, NameExpr):
        if statement.value.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.value.name}")
        expr_kind = symbols[statement.value.name]
        if expr_kind in {"string", "int", "bool"}:
            return c_print_value(expr_kind, statement.value.name, indent)

    raise LaiCompileError(f"line {statement.line}: invalid print argument")
