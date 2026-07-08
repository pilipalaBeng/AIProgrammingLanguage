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


ALLOWED_PARAM_TYPES = {"string", "int", "bool"}


# checker 只关心“这段 AST 合不合法”，不负责生成 C。
def check_program(program) -> None:
    functions = program.functions or []
    function_signatures = collect_function_signatures(functions)

    for function in functions:
        _check_statements(function.statements, _function_param_symbols(function), function_signatures)
    _check_statements(program.statements, {}, function_signatures)


def collect_function_names(functions) -> set[str]:
    return set(collect_function_signatures(functions))


def collect_function_signatures(functions) -> dict[str, list[str]]:
    names: set[str] = set()
    signatures: dict[str, list[str]] = {}
    for function in functions:
        if not NAME_RE.match(function.name):
            raise LaiCompileError(f"line {function.line}: invalid function name: {function.name}")
        if function.name in names:
            raise LaiCompileError(f"line {function.line}: function already defined: {function.name}")
        names.add(function.name)
        signatures[function.name] = _validate_params(function)
    return signatures


def _validate_params(function) -> list[str]:
    seen: set[str] = set()
    type_names: list[str] = []

    for param in function.params or []:
        if not NAME_RE.match(param.name):
            raise LaiCompileError(f"line {param.line}: invalid parameter name: {param.name}")
        if param.name in seen:
            raise LaiCompileError(f"line {param.line}: parameter already defined: {param.name}")
        if param.type_name not in ALLOWED_PARAM_TYPES:
            raise LaiCompileError(
                f"line {param.line}: invalid parameter type: {param.type_name}"
            )
        seen.add(param.name)
        type_names.append(param.type_name)

    return type_names


def _function_param_symbols(function) -> dict[str, str]:
    # 参数进入函数体局部符号表，后续 let 不能再定义同名变量。
    return {param.name: param.type_name for param in function.params or []}


def _check_statements(
    statements,
    symbols: dict[str, str],
    function_signatures: dict[str, list[str]],
) -> None:
    for statement in statements:
        _check_statement(statement, symbols, function_signatures)


def _check_statement(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, list[str]],
) -> None:
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
        if statement.name not in function_signatures:
            raise LaiCompileError(f"line {statement.line}: unknown function: {statement.name}")
        expected_types = function_signatures[statement.name]
        args = statement.args or []
        if len(args) != len(expected_types):
            raise LaiCompileError(
                f"line {statement.line}: function {statement.name} expects "
                f"{len(expected_types)} arguments, got {len(args)}"
            )
        for index, (arg, expected_type) in enumerate(zip(args, expected_types), start=1):
            actual_type = _infer_expr_type(arg, symbols, statement.line)
            if actual_type != expected_type:
                raise LaiCompileError(
                    f"line {statement.line}: argument {index} for {statement.name} "
                    f"must be {expected_type}, got {actual_type}"
                )
        return

    if isinstance(statement, IfStmt):
        condition_kind = _infer_expr_type(statement.condition, symbols, statement.line)
        if condition_kind != "bool":
            raise LaiCompileError(
                f"line {statement.line}: if condition must be bool, got {condition_kind}"
            )
        # 两个分支各用一份符号表副本，避免分支内 let 变量泄漏到外层或另一侧。
        _check_statements(statement.statements, symbols.copy(), function_signatures)
        if statement.else_statements is not None:
            _check_statements(statement.else_statements, symbols.copy(), function_signatures)
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
