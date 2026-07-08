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
from lai_core import LaiCompileError, NAME_RE


# checker 只关心“这段 AST 合不合法”，不负责生成 C。
def check_program(program) -> None:
    functions = program.functions or []
    function_names = collect_function_names(functions)

    for function in functions:
        _check_statements(function.statements, {}, function_names)
    _check_statements(program.statements, {}, function_names)


def collect_function_names(functions) -> set[str]:
    names: set[str] = set()
    for function in functions:
        if not NAME_RE.match(function.name):
            raise LaiCompileError(f"line {function.line}: invalid function name: {function.name}")
        if function.name in names:
            raise LaiCompileError(f"line {function.line}: function already defined: {function.name}")
        names.add(function.name)
    return names


def _check_statements(statements, symbols: dict[str, str], function_names: set[str]) -> None:
    for statement in statements:
        _check_statement(statement, symbols, function_names)


def _check_statement(statement, symbols: dict[str, str], function_names: set[str]) -> None:
    if isinstance(statement, LetStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name in symbols:
            raise LaiCompileError(
                f"line {statement.line}: variable already defined: {statement.name}"
            )
        symbols[statement.name] = _infer_expr_type(statement.value, symbols, statement.line)
        return

    if isinstance(statement, PrintStmt):
        _infer_expr_type(statement.value, symbols, statement.line)
        return

    if isinstance(statement, CallStmt):
        if statement.name not in function_names:
            raise LaiCompileError(f"line {statement.line}: unknown function: {statement.name}")
        return

    if isinstance(statement, IfStmt):
        condition_kind = _infer_expr_type(statement.condition, symbols, statement.line)
        if condition_kind != "bool":
            raise LaiCompileError(
                f"line {statement.line}: if condition must be bool, got {condition_kind}"
            )
        _check_statements(statement.statements, symbols.copy(), function_names)
        return

    raise LaiCompileError("internal error: unsupported statement node")


def _infer_expr_type(expr, symbols: dict[str, str], line: int) -> str:
    if isinstance(expr, StringExpr):
        return "string"
    if isinstance(expr, IntExpr):
        return "int"
    if isinstance(expr, BoolExpr):
        return "bool"
    if isinstance(expr, AddExpr):
        for term in expr.terms:
            term_kind = _infer_expr_type(term, symbols, line)
            if term_kind != "int":
                raise LaiCompileError(
                    f"line {line}: addition operands must all be int, got {term_kind}"
                )
        return "int"
    if isinstance(expr, CompareExpr):
        left_kind = _infer_expr_type(expr.left, symbols, line)
        right_kind = _infer_expr_type(expr.right, symbols, line)
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(
                f"line {line}: comparison operands must both be int, "
                f"got {left_kind} and {right_kind}"
            )
        return "bool"
    if isinstance(expr, NameExpr):
        if expr.name not in symbols:
            raise LaiCompileError(f"line {line}: unknown variable: {expr.name}")
        return symbols[expr.name]
    raise LaiCompileError("internal error: unsupported expression node")
