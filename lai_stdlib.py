def c_preamble() -> list[str]:
    return ["#include <stdio.h>"]


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
