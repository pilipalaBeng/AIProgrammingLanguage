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


class StaticIntError(ValueError):
    pass


def is_i32_min_magnitude_expr(expr) -> bool:
    while isinstance(expr, GroupExpr):
        expr = expr.value
    return (
        isinstance(expr, IntExpr)
        and type(expr.value) is int
        and expr.value == I32_MIN_MAGNITUDE
    )


def _require_i32(value: int, operation: str) -> int:
    if not I32_MIN <= value <= I32_MAX:
        raise StaticIntError(f"integer {operation} overflow")
    return value


def evaluate_static_i32(expr) -> int | None:
    if isinstance(expr, IntExpr):
        if type(expr.value) is not int:
            return None
        if not 0 <= expr.value <= I32_MAX:
            raise StaticIntError(f"integer literal out of i32 range: {expr.value}")
        return expr.value
    if isinstance(expr, GroupExpr):
        return evaluate_static_i32(expr.value)
    if isinstance(expr, UnaryExpr):
        if expr.operator == "-" and is_i32_min_magnitude_expr(expr.operand):
            return I32_MIN
        if expr.operator not in {"+", "-"}:
            return None
        value = evaluate_static_i32(expr.operand)
        if value is None:
            return None
        if expr.operator == "+":
            return value
        return _require_i32(-value, "unary negation")
    if isinstance(expr, AddExpr):
        if not expr.terms:
            return None
        result = evaluate_static_i32(expr.terms[0])
        is_dynamic = result is None
        for term in expr.terms[1:]:
            value = evaluate_static_i32(term)
            if value is None:
                is_dynamic = True
            elif not is_dynamic:
                result = _require_i32(result + value, "addition")
        return None if is_dynamic else result
    if isinstance(expr, SubtractExpr):
        left = evaluate_static_i32(expr.left)
        right = evaluate_static_i32(expr.right)
        if left is None or right is None:
            return None
        return _require_i32(left - right, "subtraction")
    if isinstance(expr, MultiplyExpr):
        if not expr.factors:
            return None
        result = evaluate_static_i32(expr.factors[0])
        is_dynamic = result is None
        for factor in expr.factors[1:]:
            value = evaluate_static_i32(factor)
            if value is None:
                is_dynamic = True
            elif not is_dynamic:
                result = _require_i32(result * value, "multiplication")
        return None if is_dynamic else result
    if isinstance(expr, DivideExpr):
        left = evaluate_static_i32(expr.left)
        right = evaluate_static_i32(expr.right)
        if right == 0:
            raise StaticIntError("division by zero")
        if left is None or right is None:
            return None
        if left == I32_MIN and right == -1:
            raise StaticIntError("integer division overflow")
        return _truncate_toward_zero(left, right)
    if isinstance(expr, ModuloExpr):
        left = evaluate_static_i32(expr.left)
        right = evaluate_static_i32(expr.right)
        if right == 0:
            raise StaticIntError("modulo by zero")
        if left is None or right is None:
            return None
        if left == I32_MIN and right == -1:
            raise StaticIntError("integer modulo overflow")
        quotient = _truncate_toward_zero(left, right)
        return left - quotient * right
    return None


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
