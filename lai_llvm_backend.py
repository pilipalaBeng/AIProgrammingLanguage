from pathlib import Path

from lai_ast import IntExpr, PrintStmt, Program
from lai_backend import Backend
from lai_checker import check_program
from lai_clang import build_with_clang
from lai_core import LaiCompileError


_I32_MAX = 2147483647


def generate_llvm(program: Program) -> str:
    check_program(program)
    return _generate_checked_llvm(program)


def _generate_checked_llvm(program: Program) -> str:
    _validate_llvm_subset(program)
    lines = [
        '@.fmt.int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"',
        "",
        "declare i32 @printf(ptr, ...)",
        "",
        "define i32 @main() {",
        "entry:",
    ]
    for index, statement in enumerate(program.statements):
        lines.append(
            f"  %print{index} = call i32 (ptr, ...) "
            f"@printf(ptr @.fmt.int, i32 {statement.value.value})"
        )
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
        if not isinstance(statement.value, IntExpr):
            raise LaiCompileError(
                f"line {statement.line}: LLVM backend does not support "
                f"{type(statement.value).__name__} yet"
            )
        if not 0 <= statement.value.value <= _I32_MAX:
            raise LaiCompileError(
                f"line {statement.line}: LLVM backend int literal out of i32 range: "
                f"{statement.value.value}"
            )


def build_llvm(llvm_path: Path, exe_path: Path) -> None:
    build_with_clang(llvm_path, exe_path)


LLVM_BACKEND = Backend(
    name="llvm",
    source_suffix=".ll",
    emit=_generate_checked_llvm,
    build=build_llvm,
)
