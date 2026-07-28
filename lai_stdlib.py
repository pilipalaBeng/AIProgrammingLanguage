def c_preamble() -> list[str]:
    return [
        "#include <stdio.h>",
        "#include <string.h>",
        "#include <limits.h>",
        "#include <stdint.h>",
        "#include <stdlib.h>",
    ]


def c_runtime_support(prefix: str) -> list[str]:
    return [
        "_Static_assert(INT_MIN == (-2147483647 - 1) && INT_MAX == 2147483647,",
        '               "LAI requires 32-bit int");',
        "",
        f"static void {prefix}_runtime_error(int line, const char* message) {{",
        '    fprintf(stderr, "LAI runtime error: line %d: %s\\n", line, message);',
        "    exit(EXIT_FAILURE);",
        "}",
        "",
        f"static int {prefix}_i32_add(int left, int right, int line) {{",
        "    int64_t result = (int64_t)left + (int64_t)right;",
        "    if (result < INT_MIN || result > INT_MAX) {",
        f'        {prefix}_runtime_error(line, "integer addition overflow");',
        "    }",
        "    return (int)result;",
        "}",
        "",
        f"static int {prefix}_i32_subtract(int left, int right, int line) {{",
        "    int64_t result = (int64_t)left - (int64_t)right;",
        "    if (result < INT_MIN || result > INT_MAX) {",
        f'        {prefix}_runtime_error(line, "integer subtraction overflow");',
        "    }",
        "    return (int)result;",
        "}",
        "",
        f"static int {prefix}_i32_multiply(int left, int right, int line) {{",
        "    int64_t result = (int64_t)left * (int64_t)right;",
        "    if (result < INT_MIN || result > INT_MAX) {",
        f'        {prefix}_runtime_error(line, "integer multiplication overflow");',
        "    }",
        "    return (int)result;",
        "}",
        "",
        f"static int {prefix}_i32_negate(int value, int line) {{",
        "    if (value == INT_MIN) {",
        f'        {prefix}_runtime_error(line, "integer unary negation overflow");',
        "    }",
        "    return -value;",
        "}",
        "",
        f"static int {prefix}_i32_divide(int left, int right, int line) {{",
        "    if (right == 0) {",
        f'        {prefix}_runtime_error(line, "division by zero");',
        "    }",
        "    if (left == INT_MIN && right == -1) {",
        f'        {prefix}_runtime_error(line, "integer division overflow");',
        "    }",
        "    return left / right;",
        "}",
        "",
        f"static int {prefix}_i32_modulo(int left, int right, int line) {{",
        "    if (right == 0) {",
        f'        {prefix}_runtime_error(line, "modulo by zero");',
        "    }",
        "    if (left == INT_MIN && right == -1) {",
        f'        {prefix}_runtime_error(line, "integer modulo overflow");',
        "    }",
        "    return left % right;",
        "}",
        "",
        f"static int {prefix}_require_positive_step(int value, int line) {{",
        "    if (value <= 0) {",
        f'        {prefix}_runtime_error(line, "for step must be greater than 0");',
        "    }",
        "    return value;",
        "}",
        "",
        f"static int {prefix}_for_advance(",
        "    int* current, int step, int end, int inclusive",
        ") {",
        "    int64_t next = (int64_t)(*current) + (int64_t)step;",
        "    if (inclusive ? next > end : next >= end) {",
        "        return 0;",
        "    }",
        "    *current = (int)next;",
        "    return 1;",
        "}",
    ]


def escape_c_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def c_print_string_literal(value: str, indent: str = "    ") -> str:
    return f"{indent}printf({escape_c_string(value + chr(10))});"


def c_print_value(value_kind: str, c_value: str, indent: str = "    ") -> str:
    if value_kind == "string":
        return f'{indent}printf("%s\\n", {c_value});'
    if value_kind in {"int", "bool"}:
        return f'{indent}printf("%d\\n", {c_value});'
    raise ValueError(f"unsupported printable LAI type: {value_kind}")
