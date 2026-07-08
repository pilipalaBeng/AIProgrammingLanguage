from lai_ast import (
    AddExpr,
    BoolExpr,
    CallExpr,
    CallStmt,
    CompareExpr,
    IfStmt,
    IntExpr,
    LetStmt,
    NameExpr,
    PrintStmt,
    ReturnStmt,
    StringExpr,
)
from lai_checker import FunctionSignature, check_program, collect_function_signatures
from lai_core import LaiCompileError, NAME_RE
from lai_stdlib import c_preamble, c_print_string_literal, c_print_value, escape_c_string


# C backend 只负责把检查过的 AST 输出成可读 C 代码。
def generate_c(program) -> str:
    check_program(program)
    functions = program.functions or []
    function_signatures = collect_function_signatures(functions)
    c_lines = [*c_preamble(), ""]

    for function in functions:
        c_lines.append(
            f"static {_function_return_type_to_c(function)} "
            f"{function.name}({_function_params_to_c(function)});"
        )

    if functions:
        c_lines.append("")

    for function in functions:
        c_lines.extend(_function_to_c(function, function_signatures))
        c_lines.append("")

    symbols: dict[str, str] = {}
    c_lines.append("int main(void) {")

    for statement in program.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_signatures))

    c_lines.append("    return 0;")
    c_lines.append("}")
    c_lines.append("")
    return "\n".join(c_lines)


def _function_to_c(function, function_signatures: dict[str, FunctionSignature]) -> list[str]:
    symbols = _function_param_symbols(function)
    c_lines = [
        f"static {_function_return_type_to_c(function)} "
        f"{function.name}({_function_params_to_c(function)}) {{"
    ]
    for statement in function.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_signatures))
    c_lines.append("}")
    return c_lines


def _function_return_type_to_c(function) -> str:
    if function.return_type is None:
        return "void"
    return _c_type_for_kind(function.return_type)


def _function_params_to_c(function) -> str:
    params = function.params or []
    if not params:
        return "void"
    return ", ".join(f"{_c_type_for_kind(param.type_name)} {param.name}" for param in params)


def _function_param_symbols(function) -> dict[str, str]:
    return {param.name: param.type_name for param in function.params or []}


def _c_type_for_kind(kind: str) -> str:
    if kind == "string":
        return "const char*"
    if kind in {"int", "bool"}:
        return "int"
    raise LaiCompileError(f"internal error: unsupported parameter type: {kind}")


def _stmt_to_c(
    statement,
    symbols: dict[str, str],
    indent_level: int,
    function_signatures: dict[str, FunctionSignature] | None = None,
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

        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures or {}
        )
        symbols[statement.name] = value_kind
        if value_kind == "string":
            return [f"{indent}const char* {statement.name} = {c_value};"]
        if value_kind in {"int", "bool"}:
            return [f"{indent}int {statement.name} = {c_value};"]
        raise LaiCompileError(f"line {statement.line}: invalid let value")

    if isinstance(statement, PrintStmt):
        return [_print_stmt_to_c(statement, symbols, function_signatures or {}, indent)]

    if isinstance(statement, CallStmt):
        return [_call_stmt_to_c(statement, function_signatures or {}, symbols, indent)]

    if isinstance(statement, ReturnStmt):
        _, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures or {}
        )
        return [f"{indent}return {c_value};"]

    if isinstance(statement, IfStmt):
        value_kind, c_condition = _expr_to_c_value(
            statement.condition, symbols, statement.line, function_signatures or {}
        )
        if value_kind != "bool":
            raise LaiCompileError(f"line {statement.line}: if condition must be bool")
        c_lines = [f"{indent}if ({c_condition}) {{"]
        then_symbols = symbols.copy()
        for inner in statement.statements:
            c_lines.extend(_stmt_to_c(inner, then_symbols, indent_level + 1, function_signatures))

        if statement.else_statements is not None:
            # else 分支也独立复制符号表，和 checker 的作用域规则保持一致。
            else_symbols = symbols.copy()
            c_lines.append(f"{indent}}} else {{")
            for inner in statement.else_statements:
                c_lines.extend(_stmt_to_c(inner, else_symbols, indent_level + 1, function_signatures))

        c_lines.append(f"{indent}}}")
        return c_lines

    raise LaiCompileError("internal error: unsupported statement node")


def _call_stmt_to_c(
    statement,
    function_signatures: dict[str, FunctionSignature],
    symbols: dict[str, str],
    indent: str,
) -> str:
    _, c_args = _call_to_c(statement.name, statement.args or [], statement.line, symbols, function_signatures)
    return f"{indent}{statement.name}({', '.join(c_args)});"


def _call_to_c(
    name: str,
    args,
    line: int,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
) -> tuple[FunctionSignature, list[str]]:
    if name not in function_signatures:
        raise LaiCompileError(f"line {line}: unknown function: {name}")
    signature = function_signatures[name]
    expected_types = signature.param_types
    if len(args) != len(expected_types):
        raise LaiCompileError(
            f"line {line}: function {name} expects {len(expected_types)} arguments, got {len(args)}"
        )

    c_args: list[str] = []
    for index, (arg, expected_type) in enumerate(zip(args, expected_types), start=1):
        actual_type, c_value = _expr_to_c_value(arg, symbols, line, function_signatures)
        if actual_type != expected_type:
            raise LaiCompileError(
                f"line {line}: argument {index} for {name} must be {expected_type}, got {actual_type}"
            )
        c_args.append(c_value)
    return signature, c_args


def _expr_to_c_value(
    expr,
    symbols: dict[str, str],
    line: int,
    function_signatures: dict[str, FunctionSignature],
) -> tuple[str, str]:
    if isinstance(expr, StringExpr):
        return "string", escape_c_string(expr.value)
    if isinstance(expr, IntExpr):
        return "int", str(expr.value)
    if isinstance(expr, BoolExpr):
        return "bool", "1" if expr.value else "0"
    if isinstance(expr, AddExpr):
        c_terms: list[str] = []
        for term in expr.terms:
            value_kind, c_value = _expr_to_c_value(term, symbols, line, function_signatures)
            if value_kind != "int":
                raise LaiCompileError(f"line {line}: invalid integer expression")
            c_terms.append(c_value)
        return "int", " + ".join(c_terms)
    if isinstance(expr, CompareExpr):
        left_kind, c_left = _expr_to_c_value(expr.left, symbols, line, function_signatures)
        right_kind, c_right = _expr_to_c_value(expr.right, symbols, line, function_signatures)
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(f"line {line}: comparison operands must be int")
        return "bool", f"{c_left} {expr.operator} {c_right}"
    if isinstance(expr, NameExpr):
        if expr.name not in symbols:
            raise LaiCompileError(f"line {line}: unknown variable: {expr.name}")
        return symbols[expr.name], expr.name
    if isinstance(expr, CallExpr):
        signature, c_args = _call_to_c(
            expr.name, expr.args or [], line, symbols, function_signatures
        )
        if signature.return_type is None:
            raise LaiCompileError(f"line {line}: function {expr.name} does not return a value")
        return signature.return_type, f"{expr.name}({', '.join(c_args)})"
    raise LaiCompileError("internal error: unsupported expression node")


def _print_stmt_to_c(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    indent: str = "    ",
) -> str:
    if isinstance(statement.value, StringExpr):
        return c_print_string_literal(statement.value.value, indent)

    expr_kind, c_value = _expr_to_c_value(
        statement.value, symbols, statement.line, function_signatures
    )
    if expr_kind in {"string", "int", "bool"}:
        return c_print_value(expr_kind, c_value, indent)

    raise LaiCompileError(f"line {statement.line}: invalid print argument")
