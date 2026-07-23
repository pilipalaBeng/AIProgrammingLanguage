from lai_ast import (
    AddExpr,
    DivideExpr,
    GroupExpr,
    IntExpr,
    ModuloExpr,
    MultiplyExpr,
    SubtractExpr,
    UnaryExpr,
)


I32_MIN = -2147483648
I32_MAX = 2147483647
I32_MIN_MAGNITUDE = 2147483648


def is_i32_min_magnitude_expr(expr) -> bool:
    while isinstance(expr, GroupExpr):
        expr = expr.value
    return (
        isinstance(expr, IntExpr)
        and type(expr.value) is int
        and expr.value == I32_MIN_MAGNITUDE
    )


def try_evaluate_static_int(expr) -> int | None:
    if isinstance(expr, IntExpr):
        return expr.value if type(expr.value) is int else None
    if isinstance(expr, GroupExpr):
        return try_evaluate_static_int(expr.value)
    if isinstance(expr, UnaryExpr):
        value = try_evaluate_static_int(expr.operand)
        if value is None:
            return None
        if expr.operator == "+":
            return value
        if expr.operator == "-":
            return -value
        return None
    if isinstance(expr, AddExpr):
        values = _evaluate_all(expr.terms)
        return sum(values) if values is not None else None
    if isinstance(expr, SubtractExpr):
        values = _evaluate_pair(expr.left, expr.right)
        return values[0] - values[1] if values is not None else None
    if isinstance(expr, MultiplyExpr):
        values = _evaluate_all(expr.factors)
        if values is None:
            return None
        result = 1
        for value in values:
            result *= value
        return result
    if isinstance(expr, DivideExpr):
        values = _evaluate_pair(expr.left, expr.right)
        if values is None or values[1] == 0:
            return None
        return _truncate_toward_zero(values[0], values[1])
    if isinstance(expr, ModuloExpr):
        values = _evaluate_pair(expr.left, expr.right)
        if values is None or values[1] == 0:
            return None
        quotient = _truncate_toward_zero(values[0], values[1])
        return values[0] - quotient * values[1]
    return None


def _evaluate_all(expressions: list) -> list[int] | None:
    if not expressions:
        return None
    values: list[int] = []
    for expression in expressions:
        value = try_evaluate_static_int(expression)
        if value is None:
            return None
        values.append(value)
    return values


def _evaluate_pair(left_expr, right_expr) -> tuple[int, int] | None:
    left = try_evaluate_static_int(left_expr)
    right = try_evaluate_static_int(right_expr)
    if left is None or right is None:
        return None
    return left, right


def _truncate_toward_zero(left: int, right: int) -> int:
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient
