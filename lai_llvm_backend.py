from pathlib import Path

from lai_ast import (
    AddExpr,
    GroupExpr,
    IntExpr,
    MultiplyExpr,
    PrintStmt,
    Program,
    SubtractExpr,
)
from lai_backend import Backend
from lai_checker import check_program
from lai_clang import build_with_clang
from lai_core import LaiCompileError


_I32_MIN = -2147483648
_I32_MAX = 2147483647
_I32_MODULUS = 4294967296


def _wrap_i32(value: int) -> int:
    return ((value - _I32_MIN) % _I32_MODULUS) + _I32_MIN


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
        if isinstance(expr, IntExpr):
            return self._lower_int_literal(expr, line)
        if isinstance(expr, GroupExpr):
            return self.lower_int_expr(expr.value, line)
        if isinstance(expr, AddExpr):
            return self._lower_chain(expr.terms, "add", line)
        if isinstance(expr, SubtractExpr):
            left_operand, left_value = self.lower_int_expr(expr.left, line)
            right_operand, right_value = self.lower_int_expr(expr.right, line)
            result = self._emit_binary("sub", left_operand, right_operand)
            return result, _wrap_i32(left_value - right_value)
        if isinstance(expr, MultiplyExpr):
            return self._lower_chain(expr.factors, "mul", line)
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
        if not 0 <= expr.value <= _I32_MAX:
            raise LaiCompileError(
                f"line {line}: LLVM backend int literal out of i32 range: "
                f"{expr.value}"
            )
        return str(expr.value), expr.value

    def _lower_chain(
        self, expressions: list, opcode: str, line: int
    ) -> tuple[str, int]:
        operand, value = self.lower_int_expr(expressions[0], line)
        for expression in expressions[1:]:
            right_operand, right_value = self.lower_int_expr(expression, line)
            operand = self._emit_binary(opcode, operand, right_operand)
            if opcode == "add":
                value = _wrap_i32(value + right_value)
            else:
                value = _wrap_i32(value * right_value)
        return operand, value

    def _emit_binary(
        self, opcode: str, left_operand: str, right_operand: str
    ) -> str:
        result = f"%value{self.next_value_index}"
        self.next_value_index += 1
        self.body_lines.append(
            f"  {result} = {opcode} i32 {left_operand}, {right_operand}"
        )
        return result


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

    for statement in program.statements:
        if not isinstance(statement, PrintStmt):
            raise LaiCompileError(
                f"line {statement.line}: LLVM backend does not support "
                f"{type(statement).__name__} yet"
            )


def build_llvm(llvm_path: Path, exe_path: Path) -> None:
    build_with_clang(llvm_path, exe_path)


LLVM_BACKEND = Backend(
    name="llvm",
    source_suffix=".ll",
    emit=_generate_checked_llvm,
    build=build_llvm,
)
