from dataclasses import dataclass
from pathlib import Path

from lai_ast import (
    AddExpr,
    ArrayExpr,
    AssignStmt,
    BoolExpr,
    BreakStmt,
    CallExpr,
    CallStmt,
    CompareExpr,
    ContinueStmt,
    DivideAssignStmt,
    DivideExpr,
    ForStmt,
    GroupExpr,
    IfStmt,
    IndexExpr,
    IntExpr,
    LetStmt,
    LogicalExpr,
    LogicalNotExpr,
    MinusAssignStmt,
    ModuloAssignStmt,
    ModuloExpr,
    MultiplyAssignStmt,
    MultiplyExpr,
    NameExpr,
    PlusAssignStmt,
    PrintStmt,
    ReturnStmt,
    StringExpr,
    SubtractExpr,
    UnaryExpr,
    WhileStmt,
)
from lai_checker import (
    EQUALITY_COMPARISON_OPERATORS,
    LOGICAL_OPERATORS,
    ORDERING_COMPARISON_OPERATORS,
    FunctionSignature,
    check_program,
    collect_function_signatures,
)
from lai_backend import Backend
from lai_clang import build_with_clang
from lai_core import LaiCompileError, NAME_RE
from lai_int import StaticIntError, evaluate_static_i32, is_i32_min_magnitude_expr
from lai_stdlib import (
    c_array_runtime_support,
    c_preamble,
    c_print_string_literal,
    c_print_value,
    c_runtime_support,
    escape_c_string,
)
from lai_types import ARRAY_TYPES, ArrayType, array_target_name


def _evaluate_checked_static_int(expr, line: int) -> int | None:
    try:
        return evaluate_static_i32(expr)
    except StaticIntError as exc:
        raise LaiCompileError(f"line {line}: {exc}") from exc


@dataclass
class _CGenerationContext:
    prefix: str
    next_temp_index: int = 0
    uses_arrays: bool = False

    def runtime_name(self, suffix: str) -> str:
        return f"{self.prefix}_{suffix}"

    def new_temp(self, label: str) -> str:
        self.next_temp_index += 1
        return f"{self.prefix}_{label}_{self.next_temp_index}"


@dataclass(frozen=True)
class CArrayBinding:
    array_type: ArrayType
    storage_name: str


def _select_runtime_prefix(program) -> str:
    user_names: set[str] = set()
    for function in program.functions or []:
        user_names.add(function.name)
        user_names.update(param.name for param in function.params or [])
        _collect_statement_identifiers(function.statements, user_names)
    _collect_statement_identifiers(program.statements, user_names)

    prefix = "__lai_internal"
    while any(name == prefix or name.startswith(f"{prefix}_") for name in user_names):
        prefix += "_"
    return prefix


def _collect_statement_identifiers(statements, user_names: set[str]) -> None:
    assignment_statements = (
        LetStmt,
        AssignStmt,
        PlusAssignStmt,
        MinusAssignStmt,
        MultiplyAssignStmt,
        DivideAssignStmt,
        ModuloAssignStmt,
    )
    for statement in statements:
        if isinstance(statement, assignment_statements):
            user_names.add(statement.name)
        if isinstance(statement, (IfStmt, WhileStmt, ForStmt)):
            if isinstance(statement, ForStmt):
                user_names.add(statement.name)
            _collect_statement_identifiers(statement.statements, user_names)
        if isinstance(statement, IfStmt) and statement.else_statements is not None:
            _collect_statement_identifiers(statement.else_statements, user_names)


# C backend 只负责把检查过的 AST 输出成可读 C 代码。
def generate_c(program) -> str:
    check_program(program)
    return _generate_checked_c(program)


def _generate_checked_c(program) -> str:
    functions = program.functions or []
    function_signatures = collect_function_signatures(functions)
    context = _CGenerationContext(_select_runtime_prefix(program))
    c_lines = [*c_preamble(), "", *c_runtime_support(context.prefix), ""]

    for function in functions:
        c_lines.append(
            f"static {_function_return_type_to_c(function)} "
            f"{function.name}({_function_params_to_c(function)});"
        )

    if functions:
        c_lines.append("")

    for function in functions:
        c_lines.extend(_function_to_c(function, function_signatures, context))
        c_lines.append("")

    symbols: dict[str, str | CArrayBinding] = {}
    c_lines.append("int main(void) {")

    for statement in program.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_signatures, context))
    c_lines.extend(["    return 0;", "}", ""])
    if context.uses_arrays:
        preamble_end = len(c_preamble())
        c_lines[preamble_end:preamble_end] = ["", *c_array_runtime_support(context.prefix)]
    return "\n".join(c_lines)


def build_c(c_path: Path, exe_path: Path) -> None:
    build_with_clang(c_path, exe_path)


C_BACKEND = Backend(
    name="c",
    source_suffix=".c",
    emit=_generate_checked_c,
    build=build_c,
)


def _function_to_c(
    function,
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
) -> list[str]:
    symbols = _function_param_symbols(function)
    c_lines = [
        f"static {_function_return_type_to_c(function)} "
        f"{function.name}({_function_params_to_c(function)}) {{"
    ]
    for statement in function.statements:
        c_lines.extend(_stmt_to_c(statement, symbols, 1, function_signatures, context))
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


def _function_param_symbols(function) -> dict[str, str | CArrayBinding]:
    return {param.name: param.type_name for param in function.params or []}


def _c_type_for_kind(kind: str) -> str:
    if kind == "string":
        return "const char*"
    if kind in {"int", "bool"}:
        return "int"
    raise LaiCompileError(f"internal error: unsupported parameter type: {kind}")


def _stmt_to_c(
    statement,
    symbols: dict[str, str | CArrayBinding],
    indent_level: int,
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
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

        if statement.type_name is not None:
            return _array_declaration_to_c(statement, symbols, function_signatures, context, indent)

        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        symbols[statement.name] = value_kind
        if value_kind == "string":
            return [f"{indent}const char* {statement.name} = {c_value};"]
        if value_kind in {"int", "bool"}:
            return [f"{indent}int {statement.name} = {c_value};"]
        raise LaiCompileError(f"line {statement.line}: invalid let value")

    if isinstance(statement, AssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if isinstance(expected_kind, CArrayBinding):
            raise LaiCompileError(f"line {statement.line}: whole-array assignment is not supported yet")
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != expected_kind:
            raise LaiCompileError(
                f"line {statement.line}: cannot assign {value_kind} "
                f"to {statement.name} of type {expected_kind}"
            )
        return [f"{indent}{statement.name} = {c_value};"]

    if isinstance(statement, PlusAssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if expected_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use += with {statement.name} "
                f"of type {expected_kind}"
            )
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: += value must be int, got {value_kind}"
            )
        helper = context.runtime_name("i32_add")
        return [f"{indent}{statement.name} = {helper}({statement.name}, {c_value}, {statement.line});"]

    if isinstance(statement, MinusAssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if expected_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use -= with {statement.name} "
                f"of type {expected_kind}"
            )
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: -= value must be int, got {value_kind}"
            )
        helper = context.runtime_name("i32_subtract")
        return [f"{indent}{statement.name} = {helper}({statement.name}, {c_value}, {statement.line});"]

    if isinstance(statement, MultiplyAssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if expected_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use *= with {statement.name} "
                f"of type {expected_kind}"
            )
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: *= value must be int, got {value_kind}"
            )
        helper = context.runtime_name("i32_multiply")
        return [f"{indent}{statement.name} = {helper}({statement.name}, {c_value}, {statement.line});"]

    if isinstance(statement, DivideAssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if expected_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use /= with {statement.name} "
                f"of type {expected_kind}"
            )
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: /= value must be int, got {value_kind}"
            )
        helper = context.runtime_name("i32_divide")
        return [f"{indent}{statement.name} = {helper}({statement.name}, {c_value}, {statement.line});"]

    if isinstance(statement, ModuloAssignStmt):
        if statement.name not in symbols:
            raise LaiCompileError(f"line {statement.line}: unknown variable: {statement.name}")
        expected_kind = symbols[statement.name]
        if expected_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: cannot use %= with {statement.name} "
                f"of type {expected_kind}"
            )
        value_kind, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        if value_kind != "int":
            raise LaiCompileError(
                f"line {statement.line}: %= value must be int, got {value_kind}"
            )
        helper = context.runtime_name("i32_modulo")
        return [f"{indent}{statement.name} = {helper}({statement.name}, {c_value}, {statement.line});"]

    if isinstance(statement, PrintStmt):
        return [_print_stmt_to_c(statement, symbols, function_signatures, context, indent)]

    if isinstance(statement, CallStmt):
        return [_call_stmt_to_c(statement, function_signatures, symbols, context, indent)]

    if isinstance(statement, BreakStmt):
        return [f"{indent}break;"]

    if isinstance(statement, ContinueStmt):
        return [f"{indent}continue;"]

    if isinstance(statement, ReturnStmt):
        _, c_value = _expr_to_c_value(
            statement.value, symbols, statement.line, function_signatures, context
        )
        return [f"{indent}return {c_value};"]

    if isinstance(statement, IfStmt):
        value_kind, c_condition = _expr_to_c_value(
            statement.condition, symbols, statement.line, function_signatures, context
        )
        if value_kind != "bool":
            raise LaiCompileError(f"line {statement.line}: if condition must be bool")
        c_lines = [f"{indent}if ({c_condition}) {{"]
        then_symbols = symbols.copy()
        for inner in statement.statements:
            c_lines.extend(
                _stmt_to_c(inner, then_symbols, indent_level + 1, function_signatures, context)
            )

        if statement.else_statements is not None:
            # else 分支也独立复制符号表，和 checker 的作用域规则保持一致。
            else_symbols = symbols.copy()
            c_lines.append(f"{indent}}} else {{")
            for inner in statement.else_statements:
                c_lines.extend(
                    _stmt_to_c(inner, else_symbols, indent_level + 1, function_signatures, context)
                )

        c_lines.append(f"{indent}}}")
        return c_lines

    if isinstance(statement, WhileStmt):
        value_kind, c_condition = _expr_to_c_value(
            statement.condition, symbols, statement.line, function_signatures, context
        )
        if value_kind != "bool":
            raise LaiCompileError(f"line {statement.line}: while condition must be bool")
        c_lines = [f"{indent}while ({c_condition}) {{"]
        loop_symbols = symbols.copy()
        for inner in statement.statements:
            c_lines.extend(
                _stmt_to_c(inner, loop_symbols, indent_level + 1, function_signatures, context)
            )
        c_lines.append(f"{indent}}}")
        return c_lines

    if isinstance(statement, ForStmt):
        if statement.name in symbols:
            raise LaiCompileError(
                f"line {statement.line}: variable already defined: {statement.name}"
            )
        start_kind, c_start = _expr_to_c_value(
            statement.start, symbols, statement.line, function_signatures, context
        )
        if start_kind != "int":
            raise LaiCompileError(f"line {statement.line}: for start must be int")
        end_kind, c_end = _expr_to_c_value(
            statement.end, symbols, statement.line, function_signatures, context
        )
        if end_kind != "int":
            raise LaiCompileError(f"line {statement.line}: for end must be int")
        c_step, requires_positive_step = _for_step_to_c(
            statement, symbols, function_signatures, context
        )
        comparison = "<=" if statement.inclusive_end else "<"
        inclusive = "1" if statement.inclusive_end else "0"
        c_start_name = context.new_temp("for_start")
        c_end_name = context.new_temp("for_end")
        c_step_name = context.new_temp("for_step")
        c_has_next_name = context.new_temp("for_has_next")
        loop_indent = "    " * (indent_level + 1)
        c_step_initializer = c_step
        if requires_positive_step:
            helper = context.runtime_name("require_positive_step")
            c_step_initializer = f"{helper}({c_step}, {statement.line})"

        c_lines = [
            f"{indent}{{",
            f"{loop_indent}int {c_start_name} = {c_start};",
            f"{loop_indent}int {c_end_name} = {c_end};",
            f"{loop_indent}int {c_step_name} = {c_step_initializer};",
            f"{loop_indent}int {c_has_next_name} = 1;",
            f"{loop_indent}for (int {statement.name} = {c_start_name}; "
            f"{c_has_next_name} && {statement.name} {comparison} {c_end_name}; "
            f"{c_has_next_name} = {context.runtime_name('for_advance')}(&{statement.name}, "
            f"{c_step_name}, {c_end_name}, {inclusive})) {{",
        ]
        loop_symbols = symbols.copy()
        loop_symbols[statement.name] = "int"
        for inner in statement.statements:
            c_lines.extend(
                _stmt_to_c(inner, loop_symbols, indent_level + 2, function_signatures, context)
            )
        c_lines.extend([f"{loop_indent}}}", f"{indent}}}"])
        return c_lines

    raise LaiCompileError("internal error: unsupported statement node")


def _for_step_to_c(
    statement: ForStmt,
    symbols: dict[str, str | CArrayBinding],
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
) -> tuple[str, bool]:
    if statement.step is None:
        return "1", False
    step_kind, c_step = _expr_to_c_value(
        statement.step, symbols, statement.line, function_signatures, context
    )
    if step_kind != "int":
        raise LaiCompileError(f"line {statement.line}: for step must be int")
    static_step = _evaluate_checked_static_int(statement.step, statement.line)
    if static_step is not None and static_step <= 0:
        raise LaiCompileError(f"line {statement.line}: for step must be greater than 0")
    return c_step, static_step is None


def _call_stmt_to_c(
    statement,
    function_signatures: dict[str, FunctionSignature],
    symbols: dict[str, str | CArrayBinding],
    context: _CGenerationContext,
    indent: str,
) -> str:
    _, c_args = _call_to_c(
        statement.name,
        statement.args or [],
        statement.line,
        symbols,
        function_signatures,
        context,
    )
    return f"{indent}{statement.name}({', '.join(c_args)});"


def _call_to_c(
    name: str,
    args,
    line: int,
    symbols: dict[str, str | CArrayBinding],
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
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
        actual_type, c_value = _expr_to_c_value(
            arg, symbols, line, function_signatures, context
        )
        if actual_type != expected_type:
            raise LaiCompileError(
                f"line {line}: argument {index} for {name} must be {expected_type}, got {actual_type}"
            )
        c_args.append(c_value)
    return signature, c_args


def _array_declaration_to_c(
    statement: LetStmt,
    symbols: dict[str, str | CArrayBinding],
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
    indent: str,
) -> list[str]:
    element_type = ARRAY_TYPES.get(statement.type_name)
    if element_type is None or not isinstance(statement.value, ArrayExpr):
        raise LaiCompileError(f"line {statement.line}: invalid array declaration")
    storage_name = context.new_temp("array_storage")
    length = len(statement.value.elements)
    c_type = _c_type_for_kind(element_type)
    c_lines = [f"{indent}{c_type} {storage_name}[{max(1, length)}];"]
    # Separate full expressions preserve initialization order and one evaluation per element.
    for index, element in enumerate(statement.value.elements):
        actual_type, c_value = _expr_to_c_value(
            element, symbols, statement.line, function_signatures, context
        )
        if actual_type != element_type:
            raise LaiCompileError(
                f"line {statement.line}: array element {index + 1} must be {element_type}, got {actual_type}"
            )
        c_lines.append(f"{indent}{storage_name}[{index}] = {c_value};")
    symbols[statement.name] = CArrayBinding(ArrayType(element_type, length), storage_name)
    context.uses_arrays = True
    return c_lines


def _index_to_c_value(
    expr: IndexExpr,
    symbols: dict[str, str | CArrayBinding],
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
) -> tuple[str, str]:
    name = array_target_name(expr.target)
    binding = symbols.get(name)
    if not isinstance(binding, CArrayBinding):
        raise LaiCompileError(f"line {expr.line}: index target must be a local array")
    index_type, c_index = _expr_to_c_value(
        expr.index, symbols, expr.line, function_signatures, context
    )
    if index_type != "int":
        raise LaiCompileError(f"line {expr.line}: array index must be int, got {index_type}")
    length = binding.array_type.length
    index = _evaluate_checked_static_int(expr.index, expr.line)
    if index is not None:
        if not 0 <= index < length:
            raise LaiCompileError(
                f"line {expr.line}: array index out of bounds: index {index}, length {length}"
            )
    else:
        c_index = f"{context.runtime_name('array_index')}({c_index}, {length}, {expr.line})"
    return binding.array_type.element_type, f"{binding.storage_name}[{c_index}]"


def _expr_to_c_value(
    expr,
    symbols: dict[str, str | CArrayBinding],
    line: int,
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
) -> tuple[str, str]:
    if isinstance(expr, ArrayExpr):
        raise LaiCompileError(f"line {expr.line}: array literals require an explicit local array declaration")
    if isinstance(expr, IndexExpr):
        return _index_to_c_value(expr, symbols, function_signatures, context)
    if isinstance(expr, StringExpr):
        return "string", escape_c_string(expr.value)
    if isinstance(expr, IntExpr):
        return "int", str(expr.value)
    if isinstance(expr, BoolExpr):
        return "bool", "1" if expr.value else "0"
    if isinstance(expr, UnaryExpr):
        if expr.operator not in {"+", "-"}:
            raise LaiCompileError(
                f"line {line}: unsupported unary operator: {expr.operator}"
            )
        if expr.operator == "-" and is_i32_min_magnitude_expr(expr.operand):
            return "int", "(-2147483647 - 1)"
        operand_kind, c_operand = _expr_to_c_value(
            expr.operand, symbols, line, function_signatures, context
        )
        if operand_kind != "int":
            raise LaiCompileError(
                f"line {line}: unary {expr.operator} operand must be int, "
                f"got {operand_kind}"
            )
        if expr.operator == "+" or _evaluate_checked_static_int(expr, line) is not None:
            return "int", f"({expr.operator}({c_operand}))"
        return "int", f"{context.runtime_name('i32_negate')}({c_operand}, {line})"
    if isinstance(expr, AddExpr):
        c_terms: list[str] = []
        for term in expr.terms:
            value_kind, c_value = _expr_to_c_value(
                term, symbols, line, function_signatures, context
            )
            if value_kind != "int":
                raise LaiCompileError(f"line {line}: invalid integer expression")
            c_terms.append(c_value)
        if _evaluate_checked_static_int(expr, line) is not None:
            return "int", " + ".join(c_terms)
        c_value = c_terms[0]
        for c_term in c_terms[1:]:
            c_value = f"{context.runtime_name('i32_add')}({c_value}, {c_term}, {line})"
        return "int", c_value
    if isinstance(expr, SubtractExpr):
        left_kind, c_left = _expr_to_c_value(
            expr.left, symbols, line, function_signatures, context
        )
        right_kind, c_right = _expr_to_c_value(
            expr.right, symbols, line, function_signatures, context
        )
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(f"line {line}: subtraction operands must be int")
        if _evaluate_checked_static_int(expr, line) is not None:
            return "int", f"{c_left} - {c_right}"
        return "int", f"{context.runtime_name('i32_subtract')}({c_left}, {c_right}, {line})"
    if isinstance(expr, MultiplyExpr):
        c_factors: list[str] = []
        for factor in expr.factors:
            value_kind, c_value = _expr_to_c_value(
                factor, symbols, line, function_signatures, context
            )
            if value_kind != "int":
                raise LaiCompileError(f"line {line}: multiplication operands must be int")
            c_factors.append(c_value)
        if _evaluate_checked_static_int(expr, line) is not None:
            return "int", " * ".join(c_factors)
        c_value = c_factors[0]
        for c_factor in c_factors[1:]:
            c_value = f"{context.runtime_name('i32_multiply')}({c_value}, {c_factor}, {line})"
        return "int", c_value
    if isinstance(expr, DivideExpr):
        left_kind, c_left = _expr_to_c_value(
            expr.left, symbols, line, function_signatures, context
        )
        right_kind, c_right = _expr_to_c_value(
            expr.right, symbols, line, function_signatures, context
        )
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(f"line {line}: division operands must be int")
        if _evaluate_checked_static_int(expr, line) is not None:
            return "int", f"{c_left} / {c_right}"
        return "int", f"{context.runtime_name('i32_divide')}({c_left}, {c_right}, {line})"
    if isinstance(expr, ModuloExpr):
        left_kind, c_left = _expr_to_c_value(
            expr.left, symbols, line, function_signatures, context
        )
        right_kind, c_right = _expr_to_c_value(
            expr.right, symbols, line, function_signatures, context
        )
        if left_kind != "int" or right_kind != "int":
            raise LaiCompileError(
                f"line {line}: modulo operands must both be int, "
                f"got {left_kind} and {right_kind}"
            )
        if _evaluate_checked_static_int(expr, line) is not None:
            return "int", f"{c_left} % {c_right}"
        return "int", f"{context.runtime_name('i32_modulo')}({c_left}, {c_right}, {line})"
    if isinstance(expr, GroupExpr):
        value_kind, c_value = _expr_to_c_value(
            expr.value, symbols, line, function_signatures, context
        )
        return value_kind, f"({c_value})"
    if isinstance(expr, CompareExpr):
        if expr.operator not in (
            ORDERING_COMPARISON_OPERATORS | EQUALITY_COMPARISON_OPERATORS
        ):
            raise LaiCompileError(
                f"line {line}: unsupported comparison operator: {expr.operator}"
            )
        left_kind, c_left = _expr_to_c_value(
            expr.left, symbols, line, function_signatures, context
        )
        right_kind, c_right = _expr_to_c_value(
            expr.right, symbols, line, function_signatures, context
        )
        if expr.operator in ORDERING_COMPARISON_OPERATORS:
            if left_kind != "int" or right_kind != "int":
                raise LaiCompileError(
                    f"line {line}: ordering comparison operands must both be int, "
                    f"got {left_kind} and {right_kind}"
                )
        elif left_kind != right_kind:
            raise LaiCompileError(
                f"line {line}: equality comparison operands must have the same type, "
                f"got {left_kind} and {right_kind}"
            )
        if left_kind == "string":
            zero_comparison = "==" if expr.operator == "==" else "!="
            return "bool", f"strcmp({c_left}, {c_right}) {zero_comparison} 0"
        return "bool", f"{c_left} {expr.operator} {c_right}"
    if isinstance(expr, LogicalNotExpr):
        operand_kind, c_operand = _expr_to_c_value(
            expr.operand, symbols, line, function_signatures, context
        )
        if operand_kind != "bool":
            raise LaiCompileError(
                f"line {line}: logical not operand must be bool, got {operand_kind}"
            )
        return "bool", f"(!({c_operand}))"
    if isinstance(expr, LogicalExpr):
        if expr.operator not in LOGICAL_OPERATORS:
            raise LaiCompileError(
                f"line {line}: unsupported logical operator: {expr.operator}"
            )
        left_kind, c_left = _expr_to_c_value(
            expr.left, symbols, line, function_signatures, context
        )
        right_kind, c_right = _expr_to_c_value(
            expr.right, symbols, line, function_signatures, context
        )
        if left_kind != "bool" or right_kind != "bool":
            raise LaiCompileError(
                f"line {line}: logical {expr.operator} operands must both be bool, "
                f"got {left_kind} and {right_kind}"
            )
        c_operator = "&&" if expr.operator == "and" else "||"
        return "bool", f"(({c_left}) {c_operator} ({c_right}))"
    if isinstance(expr, NameExpr):
        if expr.name not in symbols:
            raise LaiCompileError(f"line {line}: unknown variable: {expr.name}")
        if isinstance(symbols[expr.name], CArrayBinding):
            raise LaiCompileError(f"line {line}: array {expr.name} can only be used with an index")
        return symbols[expr.name], expr.name
    if isinstance(expr, CallExpr):
        signature, c_args = _call_to_c(
            expr.name, expr.args or [], line, symbols, function_signatures, context
        )
        if signature.return_type is None:
            raise LaiCompileError(f"line {line}: function {expr.name} does not return a value")
        return signature.return_type, f"{expr.name}({', '.join(c_args)})"
    raise LaiCompileError("internal error: unsupported expression node")


def _print_stmt_to_c(
    statement,
    symbols: dict[str, str | CArrayBinding],
    function_signatures: dict[str, FunctionSignature],
    context: _CGenerationContext,
    indent: str = "    ",
) -> str:
    if isinstance(statement.value, StringExpr):
        return c_print_string_literal(statement.value.value, indent)

    expr_kind, c_value = _expr_to_c_value(
        statement.value, symbols, statement.line, function_signatures, context
    )
    if expr_kind in {"string", "int", "bool"}:
        return c_print_value(expr_kind, c_value, indent)

    raise LaiCompileError(f"line {statement.line}: invalid print argument")
