from pathlib import Path

from lai_ast import (
    AddExpr,
    DivideExpr,
    GroupExpr,
    IntExpr,
    ModuloExpr,
    MultiplyExpr,
    PrintStmt,
    Program,
    SubtractExpr,
    UnaryExpr,
)
from lai_backend import Backend
from lai_checker import check_program
from lai_clang import build_with_clang
from lai_core import LaiCompileError
from lai_int import I32_MAX, I32_MIN, is_i32_min_magnitude_expr


class _LlvmMainEmitter:
    def __init__(self) -> None:
        self.body_lines: list[str] = []
        self.next_value_index = 0

    def emit_print(self, statement: PrintStmt, print_index: int) -> None:
        operand, _ = self.lower_int_expr(statement.value, statement.line)
        self.body_lines.append(
            f"  %print{print_index} = call i32 (ptr, ...) "
            f"@printf(ptr @.fmt.int, i32 {operand})"
        )

    def lower_int_expr(self, expr, line: int) -> tuple[str, int]:
        if isinstance(expr, UnaryExpr):
            return self._lower_unary(expr, line)
        if isinstance(expr, IntExpr):
            return self._lower_int_literal(expr, line)
        if isinstance(expr, GroupExpr):
            return self.lower_int_expr(expr.value, line)
        if isinstance(expr, AddExpr):
            return self._lower_chain(expr.terms, "AddExpr", "add", line)
        if isinstance(expr, SubtractExpr):
            left_operand, left_value = self.lower_int_expr(expr.left, line)
            right_operand, right_value = self.lower_int_expr(expr.right, line)
            result = self._emit_binary("sub", left_operand, right_operand)
            return result, left_value - right_value
        if isinstance(expr, MultiplyExpr):
            return self._lower_chain(expr.factors, "MultiplyExpr", "mul", line)
        if isinstance(expr, DivideExpr):
            return self._lower_division_like(
                expr.left,
                expr.right,
                "sdiv",
                line,
            )
        if isinstance(expr, ModuloExpr):
            return self._lower_division_like(
                expr.left,
                expr.right,
                "srem",
                line,
            )
        raise LaiCompileError(
            f"line {line}: LLVM backend does not support "
            f"{type(expr).__name__} yet"
        )

    def _lower_int_literal(self, expr: IntExpr, line: int) -> tuple[str, int]:
        if type(expr.value) is not int:
            raise LaiCompileError(
                f"line {line}: LLVM backend int literal must be int, got "
                f"{type(expr.value).__name__}"
            )
        if not 0 <= expr.value <= I32_MAX:
            raise LaiCompileError(
                f"line {line}: LLVM backend int literal out of i32 range: "
                f"{expr.value}"
            )
        return str(expr.value), expr.value

    def _lower_unary(self, expr: UnaryExpr, line: int) -> tuple[str, int]:
        if expr.operator not in {"+", "-"}:
            raise LaiCompileError(
                f"line {line}: unsupported unary operator: {expr.operator}"
            )
        if expr.operator == "-" and is_i32_min_magnitude_expr(expr.operand):
            return str(I32_MIN), I32_MIN

        operand, value = self.lower_int_expr(expr.operand, line)
        if expr.operator == "+":
            return operand, value
        if expr.operator == "-":
            result = self._emit_binary("sub", "0", operand)
            return result, -value

    def _lower_chain(
        self, expressions: list, node_name: str, opcode: str, line: int
    ) -> tuple[str, int]:
        if len(expressions) < 2:
            raise LaiCompileError(
                f"line {line}: LLVM backend {node_name} requires at least two "
                "operands"
            )
        operand, value = self.lower_int_expr(expressions[0], line)
        for expression in expressions[1:]:
            right_operand, right_value = self.lower_int_expr(expression, line)
            operand = self._emit_binary(opcode, operand, right_operand)
            if opcode == "add":
                value = value + right_value
            else:
                value = value * right_value
        return operand, value

    def _lower_division_like(
        self,
        left_expr,
        right_expr,
        opcode: str,
        line: int,
    ) -> tuple[str, int]:
        left_operand, left_value = self.lower_int_expr(left_expr, line)
        right_operand, right_value = self.lower_int_expr(right_expr, line)
        if right_value == 0:
            error_name = "division" if opcode == "sdiv" else "modulo"
            raise LaiCompileError(f"line {line}: {error_name} by zero")
        if left_value == I32_MIN and right_value == -1:
            error_name = "division" if opcode == "sdiv" else "modulo"
            raise LaiCompileError(f"line {line}: integer {error_name} overflow")

        result = self._emit_binary(opcode, left_operand, right_operand)
        quotient = _truncate_toward_zero(left_value, right_value)
        if opcode == "sdiv":
            return result, quotient
        return result, left_value - quotient * right_value

    def _emit_binary(
        self, opcode: str, left_operand: str, right_operand: str
    ) -> str:
        result = f"%value{self.next_value_index}"
        self.next_value_index += 1
        self.body_lines.append(
            f"  {result} = {opcode} i32 {left_operand}, {right_operand}"
        )
        return result


def _truncate_toward_zero(left: int, right: int) -> int:
    quotient = abs(left) // abs(right)
    if (left < 0) != (right < 0):
        return -quotient
    return quotient


def generate_llvm(program: Program) -> str:
    check_program(program)
    return _generate_checked_llvm(program)


def _generate_checked_llvm(program: Program) -> str:
    _validate_llvm_subset(program)
    emitter = _LlvmMainEmitter()
    lines = [
        '@.fmt.int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"',
        "",
        "declare i32 @printf(ptr, ...)",
        "",
        "define i32 @main() {",
        "entry:",
    ]
    for index, statement in enumerate(program.statements):
        if not isinstance(statement, PrintStmt):
            raise LaiCompileError(
                f"line {statement.line}: LLVM backend does not support "
                f"{type(statement).__name__} yet"
            )
        emitter.emit_print(statement, index)
    lines.extend(emitter.body_lines)
    lines.extend(["  ret i32 0", "}", ""])
    return "\n".join(lines)


def _validate_llvm_subset(program: Program) -> None:
    functions = program.functions or []
    if functions:
        function = functions[0]
        raise LaiCompileError(
            f"line {function.line}: LLVM backend does not support FunctionDef yet"
        )

def build_llvm(llvm_path: Path, exe_path: Path) -> None:
    build_with_clang(llvm_path, exe_path)


LLVM_BACKEND = Backend(
    name="llvm",
    source_suffix=".ll",
    emit=_generate_checked_llvm,
    build=build_llvm,
)
