# 模块索引

最后更新：2026-07-28

当前版本是 v0.36：`and` / `or` / `not` 是无符号别名的保留关键字，逻辑类型严格为 `bool`，优先级为比较 > `not` > `and` > `or`，`and` / `or` 从左到右短路。C 后端生成保留 AST 括号的 `!` / `&&` / `||`；LLVM 仍不支持 `LogicalNotExpr` / `LogicalExpr`。示例为 `examples/boolean_logic.ly`。下一版是 v0.37 运行时整数语义与安全，剩余队列为 v0.37-v0.44，共 8 个版本。

## 源码与测试

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `lai_compiler.py` | 编译器入口 | 解析 LAI v0.36，含六种基础比较以及保留关键字 `and` / `or` / `not`；逻辑层优先级为比较 > `not` > `and` > `or`，不支持符号别名。 |
| `lai_ast.py` | AST 节点 | 定义 `Program`、函数/语句节点，以及基础/算术节点、`GroupExpr`、`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、`NameExpr`、`CallExpr`。 |
| `lai_core.py` | 核心共享 | 提供 `LaiCompileError` 和 `NAME_RE`。 |
| `lai_int.py` | 整数静态事实 | 提供 i32 边界、`INT_MIN` 量级识别和纯整数字面量树静态求值。 |
| `lai_checker.py` | 语义检查 | 执行基础语义/类型检查；逻辑 operand 与结果严格为 `bool`，不引入 truthiness。 |
| `lai_backend.py` | 通用后端 | 定义不可变 `Backend` 描述符，供内部测试和未来后端注入使用。 |
| `lai_clang.py` | clang 共享构建 | 提供共享 `build_with_clang` 和既有 clang 错误措辞。 |
| `lai_c_backend.py` | C 后端 | 生成完整 C 源码；逻辑 AST 生成保留括号的 `!`、`&&`、`||`，由 C 保持从左到右短路。 |
| `lai_llvm_backend.py` | LLVM 后端 | 不依赖 `llvmlite` 发射受限文本 LLVM IR；仍只支持顶层整数 `print` 子集，`LogicalNotExpr` 和 `LogicalExpr` 明确不支持。 |
| `lai_stdlib.py` | 标准库辅助 | 管理包含 `<stdio.h>` / `<string.h>` 的 C preamble、字符串转义和 `print` 输出格式。 |
| `main.ly` | 示例输入 | 最小 LAI 程序，用于端到端验证。 |
| `examples/basic_comparisons.ly` | 比较示例输入 | C 后端六种基础比较与三种基础类型相等的可运行示例。 |
| `examples/boolean_logic.ly` | 布尔逻辑示例输入 | v0.36 C 示例，覆盖逻辑优先级、括号、双重 `not` 和从左到右短路。 |
| `examples/llvm_minimal.ly` | LLVM 示例输入 | 实验性 LLVM 后端的可运行 `print(42)` 示例。 |
| `examples/llvm_arithmetic.ly` | LLVM 示例输入 | 实验性 LLVM 后端的可运行整数算术 `print` 示例。 |
| `examples/unary_integer.ly` | 一元表达式示例输入 | 可由 C 与实验性 LLVM 后端运行的一元整数 `print` 示例。 |
| `tests/test_lai_compiler.py` | 单元测试 | 测试完整 C 路径，包括逻辑词法/解析、严格 `bool`、优先级、表达式位置和短路 C 形状。 |
| `tests/test_lai_ast.py` | 单元测试 | 测试共享 AST 节点，包括不可变的 `LogicalNotExpr`、`LogicalExpr` 和兼容导出入口。 |
| `tests/test_lai_module_boundaries.py` | 单元测试 | 测试 v0.8 拆分模块和兼容导出入口。 |
| `tests/test_lai_stdlib.py` | 单元测试 | 测试内部标准库辅助模块。 |
| `tests/test_lai_backend.py` | 单元测试 | 测试 `Backend` 不可变性、C 后端描述符、后端注入和 `clang` 构建错误。 |
| `tests/test_lai_clang.py` | 单元测试 | 测试共享 clang 调用及其错误行为。 |
| `tests/test_lai_llvm_backend.py` | 单元测试 | 测试实验性 LLVM 文本 IR 生成、整数范围，以及 `CompareExpr`、`LogicalNotExpr`、`LogicalExpr` 能力错误。 |
| `tests/test_lai_int.py` | 单元测试 | 测试 i32 静态整数求值、除法截断和 `INT_MIN` 量级识别。 |
| `tests/__init__.py` | 测试包标记 | 让 `python -m unittest tests.test_lai_compiler -v` 可稳定导入。 |

## 生成文件

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `build/main.c` | 生成 C | 由 `python lai_compiler.py main.ly --run` 生成。 |
| `build/main.exe` | 生成可执行文件 | 由 `clang` 编译生成。 |
| `examples/build/*.ll` | 生成 LLVM IR | 由 LLVM 示例命令生成的未跟踪输出。 |
| `examples/build/*.exe` | 生成 LLVM 可执行文件 | 由 LLVM 示例命令生成的未跟踪输出。 |
| `__pycache__/` | Python 缓存 | 运行测试或脚本后生成。 |
| `tests/__pycache__/` | Python 测试缓存 | 运行测试后生成。 |

## 早期实验文件

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `hello.c` | 早期 C 示例 | 不是当前编译流程的源文件。 |
| `hello.exe` | 早期可执行文件 | 不是当前编译流程的源文件。 |

## 文档

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `AGENTS.md` | agent 工作指南 | 给后续 agent 的项目约束、命令和接手顺序。 |
| `docs/ai/project-brief.md` | 项目简报 | 说明 LAI 当前定位、范围和已实现能力。 |
| `docs/ai/active-context.md` | 当前上下文 | 记录最近状态、下一步和风险。 |
| `docs/ai/roadmap.md` | 版本路线图 | 记录 v0.1 之后的阶段规划和近期边界。 |
| `docs/ai/data-structures-roadmap.md` | 数据结构命名草案 | 记录未来数组、字典等数据结构的命名方向，不代表当前已实现。 |
| `docs/ai/architecture-map.md` | 架构地图 | 说明数据流、文件职责和拆分信号。 |
| `docs/ai/conventions.md` | 项目约定 | 说明语言、测试、文档和生成物约定。 |
| `docs/ai/decisions/0001-lai-v0-compiler-scope.md` | 决策记录 | 记录 v0 使用 C 后端和极小语法范围的决定。 |
| `docs/ai/session-log/2026-07-06.md` | 会话日志 | 记录 2026-07-06 的项目进展。 |
| `docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md` | v0 设计 | v0 编译器的设计说明。 |
| `docs/superpowers/plans/2026-07-06-lai-v0-compiler.md` | v0 实施计划 | v0 编译器实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.6-type-checker-design.md` | v0.6 设计 | 基础语义/类型检查阶段的设计说明。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.6-type-checker.md` | v0.6 实施计划 | 基础语义/类型检查阶段的实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.7-stdlib-boundary-design.md` | v0.7 设计 | 小型标准库/运行时 C 输出辅助边界设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.7-stdlib-boundary.md` | v0.7 实施计划 | 小型标准库/运行时 C 输出辅助边界实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.8-module-split-design.md` | v0.8 设计 | 编译器 core/checker/C backend 拆分设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.8-module-split.md` | v0.8 实施计划 | 编译器 core/checker/C backend 拆分实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.9-ast-split-design.md` | v0.9 设计 | AST 节点拆分设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.9-ast-split.md` | v0.9 实施计划 | AST 节点拆分实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.10-else-design.md` | v0.10 设计 | 最小 `else` 语法设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.10-else.md` | v0.10 实施计划 | 最小 `else` 语法实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.11-else-if-design.md` | v0.11 设计 | `else if` 链式分支设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.11-else-if.md` | v0.11 实施计划 | `else if` 链式分支实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.12-function-parameters-design.md` | v0.12 设计 | 用户函数参数和调用实参设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.12-function-parameters.md` | v0.12 实施计划 | 用户函数参数和调用实参实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.13-function-returns-design.md` | v0.13 设计 | 函数返回值和函数调用表达式设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.13-function-returns.md` | v0.13 实施计划 | 函数返回值和函数调用表达式实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.14-branch-return-flow-design.md` | v0.14 设计 | 分支 `return` 控制流设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.14-branch-return-flow.md` | v0.14 实施计划 | 分支 `return` 控制流实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.15-while-assignment-design.md` | v0.15 设计 | 最小 `while` 循环和变量重新赋值设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.15-while-assignment.md` | v0.15 实施计划 | 最小 `while` 循环和变量重新赋值实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.16-break-continue-design.md` | v0.16 设计 | `break` / `continue` 循环控制语句设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.16-break-continue.md` | v0.16 实施计划 | `break` / `continue` 循环控制语句实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.17-loop-return-flow-design.md` | v0.17 设计 | 循环体内局部 `return` 检查设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.17-loop-return-flow.md` | v0.17 实施计划 | 循环体内局部 `return` 检查实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.18-for-loop-design.md` | v0.18 设计 | 最小 `for i from 0 to 3` 计数循环设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.18-for-loop.md` | v0.18 实施计划 | 最小 `for i from 0 to 3` 计数循环实施步骤。 |
| `docs/superpowers/specs/2026-07-09-lai-v0.19-plus-assign-design.md` | v0.19 设计 | 最小 `+=` 加法赋值语法糖设计。 |
| `docs/superpowers/plans/2026-07-09-lai-v0.19-plus-assign.md` | v0.19 实施计划 | 最小 `+=` 加法赋值语法糖实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.20-for-step-design.md` | v0.20 设计 | 最小正向 `for step` 计数循环设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.20-for-step.md` | v0.20 实施计划 | 最小正向 `for step` 计数循环实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.21-through-loop-design.md` | v0.21 设计 | 包含终点 `for through` 计数循环设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.21-through-loop.md` | v0.21 实施计划 | 包含终点 `for through` 计数循环实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.22-parenthesized-expressions-design.md` | v0.22 设计 | 括号表达式分组设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.22-parenthesized-expressions.md` | v0.22 实施计划 | 括号表达式分组实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.23-subtraction-expressions-design.md` | v0.23 设计 | 普通整数减法表达式设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.23-subtraction-expressions.md` | v0.23 实施计划 | 普通整数减法表达式实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.24-minus-assign-design.md` | v0.24 设计 | 最小 `-=` 减法赋值语法糖设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.24-minus-assign.md` | v0.24 实施计划 | 最小 `-=` 减法赋值语法糖实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.25-multiplication-expressions-design.md` | v0.25 设计 | 普通整数乘法表达式设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.25-multiplication-expressions.md` | v0.25 实施计划 | 普通整数乘法表达式实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.26-multiply-assign-design.md` | v0.26 设计 | 最小 `*=` 乘法赋值语法糖设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.26-multiply-assign.md` | v0.26 实施计划 | 最小 `*=` 乘法赋值语法糖实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.27-division-expressions-design.md` | v0.27 设计 | 普通整数除法表达式设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.27-division-expressions.md` | v0.27 实施计划 | 普通整数除法表达式实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.28-divide-assign-design.md` | v0.28 设计 | 最小 `/=` 除法赋值语法糖设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.28-divide-assign.md` | v0.28 实施计划 | 最小 `/=` 除法赋值语法糖实施步骤。 |
| `docs/superpowers/specs/2026-07-10-lai-v0.29-modulo-expressions-design.md` | v0.29 设计 | 普通整数取模表达式设计。 |
| `docs/superpowers/plans/2026-07-10-lai-v0.29-modulo-expressions.md` | v0.29 实施计划 | 普通整数取模表达式实施步骤。 |
| `docs/superpowers/specs/2026-07-11-lai-v0.30-modulo-assign-design.md` | v0.30 设计 | 最小 `%=` 取模赋值语法糖设计。 |
| `docs/superpowers/plans/2026-07-11-lai-v0.30-modulo-assign.md` | v0.30 实施计划 | 最小 `%=` 取模赋值语法糖实施步骤。 |
| `docs/superpowers/specs/2026-07-11-lai-v0.31-backend-boundary-design.md` | v0.31 设计 | 通用后端描述符与 C 后端边界设计。 |
| `docs/superpowers/plans/2026-07-11-lai-v0.31-backend-boundary.md` | v0.31 实施计划 | 后端边界、文档同步和发布验证步骤。 |
| `docs/superpowers/specs/2026-07-11-lai-v0.32-textual-llvm-backend-design.md` | v0.32 设计 | 实验性文本 LLVM IR 后端、能力边界和 CLI 选择设计。 |
| `docs/superpowers/plans/2026-07-13-lai-v0.32-textual-llvm-backend.md` | v0.32 实施计划 | 共享 clang、文本 LLVM 后端、CLI、文档和发布验证步骤。 |
| `docs/superpowers/specs/2026-07-23-lai-v0.33-llvm-integer-arithmetic-design.md` | v0.33 设计 | LLVM 整数算术表达式递归 lowering、能力边界和测试设计。 |
| `docs/superpowers/plans/2026-07-23-lai-v0.33-llvm-integer-arithmetic.md` | v0.33 实施计划 | LLVM 整数算术表达式、文档同步和发布验证步骤。 |
| `docs/superpowers/specs/2026-07-23-lai-v0.34-unary-integer-expressions-design.md` | v0.34 设计 | 前缀一元整数表达式、i32 静态边界和 LLVM unary 子集设计。 |
| `docs/superpowers/plans/2026-07-23-lai-v0.34-unary-integer-expressions.md` | v0.34 实施计划 | 已完成的一元整数表达式实现、示例和发布验证记录。 |
| `docs/superpowers/specs/2026-07-28-lai-v0.35-basic-comparisons-design.md` | v0.35 设计 | 六种基础比较、类型矩阵、字符串内容比较和 LLVM 边界设计。 |
| `docs/superpowers/plans/2026-07-28-lai-v0.35-basic-comparisons.md` | v0.35 实施计划 | 基础比较的 TDD 实现、示例、文档和发布验证记录。 |
| `docs/superpowers/specs/2026-07-28-lai-v0.36-boolean-logic-design.md` | v0.36 设计 | `and` / `or` / `not`、短路求值、严格 `bool` 类型、优先级和 LLVM 边界设计。 |
| `docs/superpowers/plans/2026-07-28-lai-v0.36-boolean-logic.md` | v0.36 实施计划 | 布尔逻辑 AST、parser、checker、C 短路生成、LLVM 边界、示例和发布验证步骤。 |
| `docs/Document/AI时代极简高性能编程语言设计方案（含专属命名+AI原生优化特性）.md` | 远期愿景 | 极简高性能语言的总体设计。 |
| `docs/Document/零基础非从业人员开发灵语（LAI）编程语言：完整工具+系统+落地步骤.md` | 落地路线 | 面向零基础开发者的工具和阶段路线。 |
