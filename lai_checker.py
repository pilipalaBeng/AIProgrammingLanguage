from dataclasses import dataclass

from lai_ast import (
    AddExpr,#加法表达式
    AssignStmt,#重新赋值语句
    BoolExpr,#布尔表达式
    BreakStmt,#跳出循环语句
    CallExpr,#调用表达式
    CallStmt,#调用语句
    CompareExpr,#比较表达式
    ContinueStmt,#继续下一轮循环语句
    DivideAssignStmt,#除法赋值语句
    DivideExpr,#除法表达式
    ForStmt,#计数循环语句
    GroupExpr,#括号分组表达式
    IfStmt,#条件语句
    IntExpr,#整数表达式
    LetStmt,#赋值语句
    MinusAssignStmt,#减法赋值语句
    MultiplyAssignStmt,#乘法赋值语句
    MultiplyExpr,#乘法表达式
    NameExpr,#变量表达式
    PlusAssignStmt,#加法赋值语句
    PrintStmt,#打印语句
    ReturnStmt,#返回语句
    StringExpr,#字符串表达式
    SubtractExpr,#减法表达式
    WhileStmt,#循环语句
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

    _check_returning_statements(
        function.statements,
        symbols,
        function_signatures,
        function.return_type,
        function.line,
        function.name,
    )


def _check_statements(
    statements,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    return_error: str = "return is only allowed in functions with return type",
    loop_depth: int = 0,
) -> None:
    for statement in statements:
        _check_statement(statement, symbols, function_signatures, return_error, loop_depth)


def _check_statement(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    return_error: str,
    loop_depth: int = 0,
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

    if isinstance(statement, AssignStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_type = symbols[statement.name]
        actual_type = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        if actual_type != expected_type:
            raise LaiCompileError(
                f"line {statement.line}: cannot assign {actual_type} "
                f"to {statement.name} of type {expected_type}"
            )
        return

    if isinstance(statement, PlusAssignStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_type = symbols[statement.name]
        if expected_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use += with {statement.name} "
                f"of type {expected_type}"
            )
        actual_type = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        if actual_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: += value must be int, got {actual_type}"
            )
        return

    if isinstance(statement, MinusAssignStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_type = symbols[statement.name]
        if expected_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use -= with {statement.name} "
                f"of type {expected_type}"
            )
        actual_type = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        if actual_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: -= value must be int, got {actual_type}"
            )
        return

    if isinstance(statement, MultiplyAssignStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_type = symbols[statement.name]
        if expected_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use *= with {statement.name} "
                f"of type {expected_type}"
            )
        actual_type = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        if actual_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: *= value must be int, got {actual_type}"
            )
        return

    if isinstance(statement, DivideAssignStmt):
        if not NAME_RE.match(statement.name):
            raise LaiCompileError(
                f"line {statement.line}: invalid variable name: {statement.name}"
            )
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_type = symbols[statement.name]
        if expected_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use /= with {statement.name} "
                f"of type {expected_type}"
            )
        actual_type = _infer_expr_type(
            statement.value, symbols, statement.line, function_signatures
        )
        if actual_type != "int":
            raise LaiCompileError(
                f"line {statement.line}: /= value must be int, got {actual_type}"
            )
        if _is_static_zero_expr(statement.value):
            raise LaiCompileError(f"line {statement.line}: division by zero")
        return

    if isinstance(statement, PrintStmt):
        _infer_expr_type(statement.value, symbols, statement.line, function_signatures)
        return

    if isinstance(statement, CallStmt):
        _check_call(statement.name, statement.args or [], statement.line, symbols, function_signatures)
        return

    if isinstance(statement, BreakStmt):
        if loop_depth <= 0:
            raise LaiCompileError(
                f"line {statement.line}: break is only allowed inside loop"
            )
        return

    if isinstance(statement, ContinueStmt):
        if loop_depth <= 0:
            raise LaiCompileError(
                f"line {statement.line}: continue is only allowed inside loop"
            )
        return

    if isinstance(statement, ReturnStmt):
        raise LaiCompileError(f"line {statement.line}: {return_error}")

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
            loop_depth,
        )
        if statement.else_statements is not None:
            _check_statements(
                statement.else_statements,
                symbols.copy(),
                function_signatures,
                return_error,
                loop_depth,
        )
        return

    if isinstance(statement, WhileStmt):
        condition_kind = _infer_expr_type(
            statement.condition, symbols, statement.line, function_signatures
        )
        if condition_kind != "bool":
            raise LaiCompileError(
                f"line {statement.line}: while condition must be bool, got {condition_kind}"
            )
        # 循环体使用符号表副本：能读写已有变量类型，但 let 新变量不泄漏到循环外。
        _check_statements(
            statement.statements,
            symbols.copy(),
            function_signatures,
            return_error,
            loop_depth + 1,
        )
        return

    if isinstance(statement, ForStmt):
        _check_for_statement(
            statement,
            symbols,
            function_signatures,
            return_error,
            loop_depth,
        )
        return

    raise LaiCompileError("internal error: unsupported statement node")


def _check_for_statement(
    statement: ForStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    return_error: str,
    loop_depth: int,
) -> None:
    if not NAME_RE.match(statement.name):
        raise LaiCompileError(
            f"line {statement.line}: invalid variable name: {statement.name}"
        )
    if statement.name in symbols:
        raise LaiCompileError(
            f"line {statement.line}: variable already defined: {statement.name}"
        )

    start_kind = _infer_expr_type(
        statement.start, symbols, statement.line, function_signatures
    )
    if start_kind != "int":
        raise LaiCompileError(
            f"line {statement.line}: for start must be int, got {start_kind}"
        )

    end_kind = _infer_expr_type(
        statement.end, symbols, statement.line, function_signatures
    )
    if end_kind != "int":
        raise LaiCompileError(
            f"line {statement.line}: for end must be int, got {end_kind}"
        )

    _check_for_step(statement, symbols, function_signatures)

    # for 的循环变量只放进循环体副本，避免泄漏到外层作用域。
    loop_symbols = symbols.copy()
    loop_symbols[statement.name] = "int"
    _check_statements(
        statement.statements,
        loop_symbols,
        function_signatures,
        return_error,
        loop_depth + 1,
    )


def _check_returning_statements(
    statements,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    function_line: int,
    function_name: str,
    loop_depth: int = 0,
) -> None:
    if not statements:
        raise LaiCompileError(f"line {function_line}: function {function_name} must end with return")

    for statement in statements[:-1]:
        _check_non_returning_statement(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )

    _check_final_returning_statement(
        statements[-1],
        symbols,
        function_signatures,
        expected_return_type,
        function_line,
        function_name,
        loop_depth,
    )


def _check_non_returning_statement(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int = 0,
) -> None:
    if isinstance(statement, ReturnStmt):
        raise LaiCompileError(
            f"line {statement.line}: return must be the final statement in its block"
        )

    if isinstance(statement, IfStmt):
        _check_if_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            must_return=False,
            loop_depth=loop_depth,
        )
        return

    if isinstance(statement, WhileStmt):
        _check_while_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        return

    if isinstance(statement, ForStmt):
        _check_for_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        return

    _check_statement(
        statement,
        symbols,
        function_signatures,
        "return must be the final statement in its block",
        loop_depth,
    )


def _check_final_returning_statement(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    function_line: int,
    function_name: str,
    loop_depth: int = 0,
) -> None:
    if isinstance(statement, ReturnStmt):
        _check_return_statement(statement, symbols, function_signatures, expected_return_type)
        return

    if isinstance(statement, IfStmt):
        _check_if_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            must_return=True,
            function_line=function_line,
            function_name=function_name,
            loop_depth=loop_depth,
        )
        return

    if isinstance(statement, WhileStmt):
        _check_while_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        raise LaiCompileError(f"line {function_line}: function {function_name} must end with return")

    if isinstance(statement, ForStmt):
        _check_for_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        raise LaiCompileError(f"line {function_line}: function {function_name} must end with return")

    _check_statement(
        statement,
        symbols,
        function_signatures,
        "return must be the final statement in its block",
        loop_depth,
    )
    raise LaiCompileError(f"line {function_line}: function {function_name} must end with return")


def _check_if_statement_for_returning_function(
    statement: IfStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    must_return: bool,
    function_line: int | None = None,
    function_name: str | None = None,
    loop_depth: int = 0,
) -> None:
    condition_kind = _infer_expr_type(
        statement.condition, symbols, statement.line, function_signatures
    )
    if condition_kind != "bool":
        raise LaiCompileError(
            f"line {statement.line}: if condition must be bool, got {condition_kind}"
        )

    # 返回值函数中，分支体也使用符号表副本，保持和普通 if 一致的局部可见性。
    then_symbols = symbols.copy()
    else_symbols = symbols.copy()

    if must_return:
        _check_returning_statements(
            statement.statements,
            then_symbols,
            function_signatures,
            expected_return_type,
            function_line or statement.line,
            function_name or "<anonymous>",
            loop_depth,
        )
        if statement.else_statements is None:
            raise LaiCompileError(
                f"line {function_line or statement.line}: "
                f"function {function_name or '<anonymous>'} must end with return"
            )
        _check_returning_statements(
            statement.else_statements,
            else_symbols,
            function_signatures,
            expected_return_type,
            function_line or statement.line,
            function_name or "<anonymous>",
            loop_depth,
        )
        return

    _check_statements(
        statement.statements,
        then_symbols,
        function_signatures,
        "return must be the final statement in its block",
        loop_depth,
    )
    if statement.else_statements is not None:
        _check_statements(
            statement.else_statements,
            else_symbols,
            function_signatures,
            "return must be the final statement in its block",
            loop_depth,
        )


def _check_while_statement_for_returning_function(
    statement: WhileStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int,
) -> None:
    condition_kind = _infer_expr_type(
        statement.condition, symbols, statement.line, function_signatures
    )
    if condition_kind != "bool":
        raise LaiCompileError(
            f"line {statement.line}: while condition must be bool, got {condition_kind}"
        )

    _check_loop_statements_for_returning_function(
        statement.statements,
        symbols.copy(),
        function_signatures,
        expected_return_type,
        loop_depth + 1,
    )


def _check_for_statement_for_returning_function(
    statement: ForStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int,
) -> None:
    if not NAME_RE.match(statement.name):
        raise LaiCompileError(
            f"line {statement.line}: invalid variable name: {statement.name}"
        )
    if statement.name in symbols:
        raise LaiCompileError(
            f"line {statement.line}: variable already defined: {statement.name}"
        )

    start_kind = _infer_expr_type(
        statement.start, symbols, statement.line, function_signatures
    )
    if start_kind != "int":
        raise LaiCompileError(
            f"line {statement.line}: for start must be int, got {start_kind}"
        )

    end_kind = _infer_expr_type(
        statement.end, symbols, statement.line, function_signatures
    )
    if end_kind != "int":
        raise LaiCompileError(
            f"line {statement.line}: for end must be int, got {end_kind}"
        )

    _check_for_step(statement, symbols, function_signatures)

    loop_symbols = symbols.copy()
    loop_symbols[statement.name] = "int"
    _check_loop_statements_for_returning_function(
        statement.statements,
        loop_symbols,
        function_signatures,
        expected_return_type,
        loop_depth + 1,
    )


def _check_for_step(
    statement: ForStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
) -> None:
    if statement.step is None:
        return

    step_kind = _infer_expr_type(
        statement.step, symbols, statement.line, function_signatures
    )
    if step_kind != "int":
        raise LaiCompileError(
            f"line {statement.line}: for step must be int, got {step_kind}"
        )
    if _is_static_zero_expr(statement.step):
        raise LaiCompileError(
            f"line {statement.line}: for step must be greater than 0"
        )


def _is_static_zero_expr(expr) -> bool:
    if isinstance(expr, IntExpr):
        return expr.value == 0
    if isinstance(expr, AddExpr):
        return all(_is_static_zero_expr(term) for term in expr.terms)
    return False


def _check_loop_statements_for_returning_function(
    statements,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int,
) -> None:
    for index, statement in enumerate(statements):
        is_final = index == len(statements) - 1
        _check_loop_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
            is_final,
        )


def _check_loop_statement_for_returning_function(
    statement,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int,
    is_final: bool,
) -> None:
    if isinstance(statement, ReturnStmt):
        if not is_final:
            raise LaiCompileError(
                f"line {statement.line}: return must be the final statement in its block"
            )
        _check_return_statement(statement, symbols, function_signatures, expected_return_type)
        return

    if isinstance(statement, IfStmt):
        _check_loop_if_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        return

    if isinstance(statement, WhileStmt):
        _check_while_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        return

    if isinstance(statement, ForStmt):
        _check_for_statement_for_returning_function(
            statement,
            symbols,
            function_signatures,
            expected_return_type,
            loop_depth,
        )
        return

    _check_statement(
        statement,
        symbols,
        function_signatures,
        "return must be the final statement in its block",
        loop_depth,
    )


def _check_loop_if_statement_for_returning_function(
    statement: IfStmt,
    symbols: dict[str, str],
    function_signatures: dict[str, FunctionSignature],
    expected_return_type: str,
    loop_depth: int,
) -> None:
    condition_kind = _infer_expr_type(
        statement.condition, symbols, statement.line, function_signatures
    )
    if condition_kind != "bool":
        raise LaiCompileError(
            f"line {statement.line}: if condition must be bool, got {condition_kind}"
        )

    _check_loop_statements_for_returning_function(
        statement.statements,
        symbols.copy(),
        function_signatures,
        expected_return_type,
        loop_depth,
    )
    if statement.else_statements is not None:
        _check_loop_statements_for_returning_function(
            statement.else_statements,
            symbols.copy(),
            function_signatures,
            expected_return_type,
            loop_depth,
        )


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
    if isinstance(expr, SubtractExpr):
        left_kind = _infer_expr_type(expr.left, symbols, line, function_signatures)
        right_kind = _infer_expr_type(expr.right, symbols, line, function_signatures)
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(
                f"line {line}: subtraction operands must both be int, "
                f"got {left_kind} and {right_kind}"
            )
        return "int"
    if isinstance(expr, MultiplyExpr):
        for factor in expr.factors:
            factor_kind = _infer_expr_type(factor, symbols, line, function_signatures)
            if factor_kind != "int":
                raise LaiCompileError(
                    f"line {line}: multiplication operands must all be int, got {factor_kind}"
                )
        return "int"
    if isinstance(expr, DivideExpr):
        left_kind = _infer_expr_type(expr.left, symbols, line, function_signatures)
        right_kind = _infer_expr_type(expr.right, symbols, line, function_signatures)
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(
                f"line {line}: division operands must both be int, "
                f"got {left_kind} and {right_kind}"
            )
        if _is_static_zero_expr(expr.right):
            raise LaiCompileError(f"line {line}: division by zero")
        return "int"
    if isinstance(expr, GroupExpr):
        return _infer_expr_type(expr.value, symbols, line, function_signatures)
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


def _is_static_zero_expr(expr) -> bool:
    if isinstance(expr, IntExpr):
        return expr.value == 0
    if isinstance(expr, GroupExpr):
        return _is_static_zero_expr(expr.value)
    return False
