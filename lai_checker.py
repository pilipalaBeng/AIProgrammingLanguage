from dataclasses import dataclass

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
from lai_core import LaiCompileError, NAME_RE


VALUE_TYPES = {"string", "int", "bool"}


@dataclass(frozen=True)
class FunctionSignature:
    param_types: list[str]
    return_type: str | None


# checker 只关心“这段 AST 合不合法”，不负责生成 C。
def check_program(program) -> None:
    functions = program.functions or []
    function_signatures = collect_function_signatures(functions)

    for function in functions:
        _check_function(function, function_signatures)
    _check_statements(program.statements, {}, function_signatures)


def collect_function_names(functions) -> set[str]:
    return set(collect_function_signatures(functions))


def collect_function_signatures(functions) -> dict[str, FunctionSignature]:
    names: set[str] = set()
    signatures: dict[str, FunctionSignature] = {}
    for function in functions:
        if not NAME_RE.match(function.name):
            raise LaiCompileError(f"line {function.line}: invalid function name: {function.name}")
        if function.name in names:
            raise LaiCompileError(f"line {function.line}: function already defined: {function.name}")
        names.add(function.name)
        param_types = _validate_params(function)
        return_type = _validate_return_type(function)
        signatures[function.name] = FunctionSignature(param_types, return_type)
    return signatures


def _validate_params(function) -> list[str]:
    seen: set[str] = set()
    type_names: list[str] = []

    for param in function.params or []:
        if not NAME_RE.match(param.name):
            raise LaiCompileError(f"line {param.line}: invalid parameter name: {param.name}")
        if param.name in seen:
            raise LaiCompileError(f"line {param.line}: parameter already defined: {param.name}")
        if param.type_name not in VALUE_TYPES:
            raise LaiCompileError(
                f"line {param.line}: invalid parameter type: {param.type_name}"
            )
        seen.add(param.name)
        type_names.append(param.type_name)

    return type_names


def _validate_return_type(function) -> str | None:
    if function.return_type is None:
        return None
    if function.return_type not in VALUE_TYPES:
        raise LaiCompileError(
            f"line {function.line}: invalid return type: {function.return_type}"
        )
    return function.return_type


def _function_param_symbols(function) -> dict[str, str]:
    # 参数进入函数体局部符号表，后续 let 不能再定义同名变量。
    return {param.name: param.type_name for param in function.params or []}


def _check_function(function, function_signatures: dict[str, FunctionSignature]) -> None:
    symbols = _function_param_symbols(function)
    if function.return_type is None:
        _check_statements(function.statements, symbols, function_signatures)
        return

    if not function.statements or not isinstance(function.statements[-1], ReturnStmt):
        raise LaiCompileError(f"line {function.line}: function {function.name} must end with return")

    # v0.13 只允许最后一条顶层语句 return，避免过早引入完整控制流分析。
    _check_statements(
        function.statements[:-1],
        symbols,
        function_signatures,
        "return must be the final top-level statement",
    )
    _check_return_statement(function.statements[-1], symbols, function_signatures, function.return_type)


def _check_statements(
    statements,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    return_error: str = "return is only allowed in functions with return type",
) -> None:
    for statement in statements:
        _check_statement(statement, symbols, function_signatures, return_error)


def _check_statement(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    return_error: str,
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
        symbols[statement.name] = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        return

    if isinstance(statement, PrintStmt):
        _infer_expr_type(statement.value, symbols, statement.line, function_signatures)
        return

    if isinstance(statement, CallStmt):
        _check_call(statement.name, statement.args or [], statement.line, symbols, function_signatures)
        return

    if isinstance(statement, ReturnStmt):
        raise LaiCompileError(f"line {statement.line}: {return_error}")
        return

    if isinstance(statement, IfStmt):
        condition_kind = _infer_expr_type(
            statement.condition, symbols, statement.line, function_signatures
        )
        if condition_kind != "bool":
            raise LaiCompileError(
                f"line {statement.line}: if condition must be bool, got {condition_kind}"
            )
        # 两个分支各用一份符号表副本，避免分支内 let 变量泄漏到外层或另一侧。
        _check_statements(
            statement.statements,
            symbols.copy(),
            function_signatures,
            return_error,
        )
        if statement.else_statements is not None:
            _check_statements(
                statement.else_statements,
                symbols.copy(),
                function_signatures,
                return_error,
            )
        return

    raise LaiCompileError("internal error: unsupported statement node")


def _check_return_statement(
    statement: ReturnStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
) -> None:
    actual_type = _infer_expr_type(statement.value, symbols, statement.line, function_signatures)
    if actual_type != expected_return_type:
        raise LaiCompileError(
            f"line {statement.line}: return type must be {expected_return_type}, got {actual_type}"
        )


def _check_call(
    name: str,
    args,
    line: int,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
) -> FunctionSignature:
    if name not in function_signatures:
        raise LaiCompileError(f"line {line}: unknown function: {name}")
    signature = function_signatures[name]
    expected_types = signature.param_types
    if len(args) != len(expected_types):
        raise LaiCompileError(
            f"line {line}: function {name} expects {len(expected_types)} arguments, got {len(args)}"
        )
    for index, (arg, expected_type) in enumerate(zip(args, expected_types), start=1):
        actual_type = _infer_expr_type(arg, symbols, line, function_signatures)
        if actual_type != expected_type:
            raise LaiCompileError(
                f"line {line}: argument {index} for {name} must be {expected_type}, got {actual_type}"
            )
    return signature


def _infer_expr_type(
    expr,
    symbols: dict[str, str],
    line: int,
    function_signatures: dict[str, FunctionSignature],
) -> str:
    if isinstance(expr, StringExpr):
        return "string"
    if isinstance(expr, IntExpr):
        return "int"
    if isinstance(expr, BoolExpr):
        return "bool"
    if isinstance(expr, AddExpr):
        for term in expr.terms:
            term_kind = _infer_expr_type(term, symbols, line, function_signatures)
            if term_kind != "int":
                raise LaiCompileError(
                    f"line {line}: addition operands must all be int, got {term_kind}"
                )
        return "int"
    if isinstance(expr, CompareExpr):
        left_kind = _infer_expr_type(expr.left, symbols, line, function_signatures)
        right_kind = _infer_expr_type(expr.right, symbols, line, function_signatures)
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
    if isinstance(expr, CallExpr):
        signature = _check_call(expr.name, expr.args or [], line, symbols, function_signatures)
        if signature.return_type is None:
            raise LaiCompileError(f"line {line}: function {expr.name} does not return a value")
        return signature.return_type
    raise LaiCompileError("internal error: unsupported expression node")
