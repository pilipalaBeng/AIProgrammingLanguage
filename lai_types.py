from dataclasses import dataclass

from lai_ast import Expr, GroupExpr, NameExpr


ARRAY_TYPES = {"int[]": "int", "string[]": "string", "bool[]": "bool"}


@dataclass(frozen=True)
class ArrayType:
    element_type: str
    length: int

    def __str__(self) -> str:
        return f"{self.element_type}[]"


def array_target_name(target: Expr) -> str | None:
    while isinstance(target, GroupExpr):
        target = target.value
    return target.name if isinstance(target, NameExpr) else None
