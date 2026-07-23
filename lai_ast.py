from dataclasses import dataclass


# AST 节点只描述源码结构，不负责检查和生成代码。
# 这样 parser、checker、backend 可以共享同一套节点类型。
@dataclass(frozen=True)
class Program:
    statements: list["Stmt"]
    functions: list["FunctionDef"] | None = None


class Stmt:
    pass


@dataclass(frozen=True)
class FunctionDef:
    name: str
    statements: list["Stmt"]
    line: int
    params: list["Param"] | None = None
    return_type: str | None = None


@dataclass(frozen=True)
class Param:
    name: str
    type_name: str
    line: int


@dataclass(frozen=True)
class LetStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class AssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class PlusAssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class MinusAssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class MultiplyAssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class DivideAssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class ModuloAssignStmt(Stmt):
    name: str
    value: "Expr"
    line: int


@dataclass(frozen=True)
class PrintStmt(Stmt):
    value: "Expr"
    line: int


@dataclass(frozen=True)
class IfStmt(Stmt):
    condition: "Expr"
    statements: list["Stmt"]
    line: int
    # None 表示没有 else；空列表表示写了 else 但分支体为空。
    else_statements: list["Stmt"] | None = None


@dataclass(frozen=True)
class WhileStmt(Stmt):
    condition: "Expr"
    statements: list["Stmt"]
    line: int


@dataclass(frozen=True)
class ForStmt(Stmt):
    name: str
    start: "Expr"
    end: "Expr"
    statements: list["Stmt"]
    line: int
    step: "Expr | None" = None
    inclusive_end: bool = False


@dataclass(frozen=True)
class BreakStmt(Stmt):
    line: int


@dataclass(frozen=True)
class ContinueStmt(Stmt):
    line: int


@dataclass(frozen=True)
class CallStmt(Stmt):
    name: str
    line: int
    args: list["Expr"] | None = None


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    value: "Expr"
    line: int


class Expr:
    pass


@dataclass(frozen=True)
class StringExpr(Expr):
    value: str


@dataclass(frozen=True)
class IntExpr(Expr):
    value: int


@dataclass(frozen=True)
class UnaryExpr(Expr):
    operator: str
    operand: "Expr"


@dataclass(frozen=True)
class AddExpr(Expr):
    terms: list["Expr"]


@dataclass(frozen=True)
class SubtractExpr(Expr):
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class MultiplyExpr(Expr):
    factors: list["Expr"]


@dataclass(frozen=True)
class DivideExpr(Expr):
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class ModuloExpr(Expr):
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class GroupExpr(Expr):
    value: "Expr"


@dataclass(frozen=True)
class BoolExpr(Expr):
    value: bool


@dataclass(frozen=True)
class CompareExpr(Expr):
    left: "Expr"
    operator: str
    right: "Expr"


@dataclass(frozen=True)
class NameExpr(Expr):
    name: str


@dataclass(frozen=True)
class CallExpr(Expr):
    name: str
    args: list["Expr"] | None
    line: int
