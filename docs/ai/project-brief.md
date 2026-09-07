# LAI 项目简报

最后更新：2026-09-07

## 项目一句话

LAI（灵语）是一个面向 AI 时代的极简高性能编程语言实验项目。当前仓库落地的是
v0.40 第一阶段编译器原型：提供从 `.ly` 翻译到 C、再编译运行的完整默认闭环，在固定长度局部数组上新增元素修改，同时保留受限的实验性文本 LLVM IR 后端。长度 API 和遍历仍在 v0.40 待实现。

## 当前阶段目标

当前阶段只追求一个可靠的最小版本：

```text
main.ly -> lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang -> build/main.exe
```

这一步的意义不是完成语言本体，而是证明：

- 能定义一个稳定的 LAI 源文件格式。
- 能解析并校验极小语法。
- 能生成可编译的 C 代码。
- 能通过测试和命令行示例验证结果。

## 当前已实现能力

语言层面：

- 显式局部数组声明：`let scores: int[] = [90, 95, 100]`；支持同构固定长度 `int[]`、`string[]`、`bool[]` 和有类型的空数组 `let empty: int[] = []`
- 初始化元素从左到右各求值一次；`scores[index]` 读取和修改要求从 0 开始的 `int` 索引
- 三种数组元素允许同型 `=`，仅 `int` 元素支持 `+= -= *= /= %=`；先索引求值及边界检查，再旧值（复合赋值），再右值，均单次执行，成功才写入，长度不变
- 元素修改保留 checked i32、静态零除和静态/动态边界检查；索引失败不执行右值，右值或算术失败不写入
- 静态可算出的越界在编译期拒绝；动态越界在访问前向 `stderr` 输出行号、index、length 并以 `EXIT_FAILURE` 退出
- 数组可在 main、用户函数、分支和循环的局部作用域声明；索引结果是标量，可用于现有表达式、打印、函数标量实参和返回
- 程序入口：`fn main() { ... }`
- 用户函数：`fn greet() { ... }`
- 带参数用户函数：`fn show(name: string, count: int, ready: bool) { ... }`
- 带返回值用户函数：`fn add(a: int, b: int) -> int { return a + b }`
- 返回值函数支持条件、嵌套分支和循环路径中的通用 `return expr`，包括 guard clause
- 所有可达路径必须精确返回；第一条不可达语句报 `line N: unreachable statement`
- `while true { return value }` 及任意括号包裹的 `(true)` 可作为保证返回路径
- 函数调用语句：`greet()`、`show("JD", 3, true)`
- 函数调用表达式：`let count = add(1, 2)`、`print(add(1, 2))`
- 最小循环：`while count < 3 { ... }`
- 变量重新赋值：`count = count + 1`
- 加法赋值语法糖：`count += 1`
- 减法赋值语法糖：`count -= 1`
- 乘法赋值语法糖：`count *= 2`
- 除法赋值语法糖：`count /= 2`
- 取模赋值语法糖：`count %= 3`
- 循环跳出：`break`
- 跳过本轮循环：`continue`
- 返回值函数中的循环路径返回：`while count < limit { if count > 2 { return count } }`；普通循环仍需要外部兜底
- 计数循环：`for i from 0 to 3 { print(i) }`，`to` 不包含终点
- 计数循环步长：`for i from 0 to 6 step 2 { print(i) }`
- 包含终点计数循环：`for i from 0 through 3 { print(i) }`
- 正式源码扩展名：`.ly`
- 单行注释：`// comment`
- 字符串变量：`let name = "LingYu"`
- 整数变量：`let count = 123`
- 整数加法变量：`let count = 1 + 2`
- 括号表达式：`let count = (1 + 2)`、`print((1 + 2))`、`if (ready) { ... }`
- 整数减法表达式：`let count = 5 - 2`、`print(5 - 2)`、`return a - b`
- 整数乘法表达式：`let count = 2 * 3`、`print(2 + 3 * 4)`、`return a * b`
- 整数除法表达式：`let count = 8 / 2`、`print(8 + 6 / 2)`、`return a / b`
- 整数取模表达式：`let count = 7 % 3`、`print(8 + 7 % 3)`、`return a % b`
- 最小算术优先级：`*`、`/` 和 `%` 高于 `+` / `-`，括号可覆盖分组
- 显式静态除零检查：`8 / 0` 和 `8 / (0)` 会报 `division by zero`
- 显式静态 `/=` 除零检查：`count /= 0` 和 `count /= (0)` 会报 `division by zero`
- 显式静态取模除零检查：`7 % 0` 和 `7 % (0)` 会报 `modulo by zero`
- 显式静态 `%=` 取模除零检查：`count %= 0` 和 `count %= (0)` 会报 `modulo by zero`
- 布尔变量：`let ready = true`
- 比较表达式变量：`let ok = count == 3`
- 完整基础比较：`<`、`<=`、`>`、`>=`、`==`、`!=`
- 大小比较只接受两个 `int`；相等比较接受同类型的 `int`、`bool` 或 `string`
- 字符串 `==` / `!=` 按内容比较，C 后端生成 `strcmp(...) == 0` / `!= 0`
- 未分组比较链会报 `comparison chains are not supported`
- 布尔逻辑关键字：`and`、`or`、`not`，三者均为保留关键字；不支持 `&&`、`||`、`!` 源码别名
- 严格布尔规则：逻辑 operand 与结果均为 `bool`，不支持 truthiness
- 逻辑优先级：比较高于 `not`，`not` 高于 `and`，`and` 高于 `or`
- `and` / `or` 运行时从左到右短路，C 后端生成保留 AST 括号的 `!`、`&&`、`||`
- 打印字面量：`print("Hello LAI")`
- 打印整数字面量、加法表达式、减法表达式、乘法表达式、除法表达式和取模表达式：`print(123)`、`print(1 + 2)`、`print(5 - 2)`、`print(2 * 3)`、`print(8 / 2)`、`print(7 % 3)`
- 打印布尔值和比较结果：`print(true)`、`print(1 < 2)`
- 打印变量：`print(name)`
- 条件语句：`if ready { ... }`、`if is_ready(count) { ... }`、`if 1 < 2 { ... }`、`if false { ... } else { ... }`、`if false { ... } else if true { ... } else { ... }`

编译器层面：

- `compile_source(source: str, backend: Backend = C_BACKEND) -> str`
- `check_program(program: Program) -> None`
- `compile_file(source_path: Path, build_dir: Path, backend: Backend = C_BACKEND) -> tuple[Path, Path]`
- `lai_ast.py` 集中定义 AST 节点
- `ArrayExpr`、`IndexExpr` 表示数组字面量和索引；`LetStmt.type_name` 默认 `None`，兼容旧构造
- `lai_types.py` 共享 `ArrayType(element_type, length)` 和局部数组目标解析辅助
- `lai_core.py` 共享错误类型和核心名称规则
- `lai_checker.py` 承载语义/类型检查
- `lai_checker.py` 内部 `FlowOutcome` 结果集统一表示 fallthrough、return、break、continue 和 divergence；它不是 LAI 源码语法
- `lai_backend.py` 承载不可变的通用 `Backend` 描述符
- `lai_clang.py` 承载共享 `clang` 调用和既有错误措辞
- `lai_c_backend.py` 承载完整 C 源码生成、构建和默认 `C_BACKEND`
- `CArrayBinding` 关联局部数组类型与内部 C 存储名；初始化逐条写入，空数组物理占位 1、逻辑长度 0
- `lai_llvm_backend.py` 承载不依赖 `llvmlite` 的实验性文本 LLVM IR 生成和 `LLVM_BACKEND`
- `lai_stdlib.py` 内部管理包含 `<stdio.h>` / `<string.h>` 的 C preamble、字符串转义和 `print` 输出格式
- 命令行入口：`python lai_compiler.py main.ly --run`
- `--backend {c,llvm}` 固定后端选择，默认 `c`；`examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly` 是可运行 LLVM 示例
- `LogicalNotExpr` 与 `LogicalExpr` 分别表示逻辑非和逻辑与/或
- LLVM 支持空 `main` 或顶层 `print` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；`LogicalNotExpr`、`LogicalExpr` 等范围外的有效 LAI 会报明确能力错误
- 行号化错误：缺失 `main`、未知变量、未知函数、非法变量名、重复变量、非法字符串、非布尔 `if` 条件、非整数加法/比较、参数错误、返回值错误等
- 生成 C 并调用 `clang`
- 默认编译流程解析和检查后委托 `C_BACKEND`；内部测试和未来后端可注入 `Backend`

测试层面：

- `tests/test_lai_compiler.py` 覆盖词法、解析、语义/类型检查、C 生成、字符串打印、整数变量、整数字面量打印、整数算术、优先级、括号表达式、注释、布尔值、六种比较、逻辑表达式、严格布尔、短路 C 形状、比较类型矩阵、字符串内容比较、比较链错误、`if`、`else`、`else if`、`while`、`for`、赋值、复合赋值、循环控制、用户函数、返回控制流、运行时安全示例编译和错误处理。
- `tests/test_lai_ast.py` 覆盖共享 AST 节点、`else` 分支节点、`else if` 嵌套节点、`ReturnStmt`、`CallExpr`、`GroupExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`AssignStmt`、`MinusAssignStmt`、`MultiplyAssignStmt`、`DivideAssignStmt`、`ModuloAssignStmt`、`WhileStmt`、`ForStmt`、`BreakStmt`、`ContinueStmt` 和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖内部标准库/运行时 C 输出辅助模块。
- `tests/test_lai_clang.py` 覆盖共享 clang 调用和错误行为。
- `tests/test_lai_llvm_backend.py` 覆盖实验性 LLVM 文本 IR 的生成、能力错误、整数范围，以及合法比较和布尔逻辑分别保持 `CompareExpr`、`LogicalNotExpr`、`LogicalExpr` 能力错误。
- `tests/test_lai_runtime.py` 使用真实 `clang` 覆盖动态整数错误、逻辑短路、动态 step 单次求值、`continue` / `break` 和 i32 上界范围完成。
- `tests/test_lai_flow.py` 覆盖 guard clause、不可达诊断、精确所有路径返回、静态 true 循环和嵌套发散传播。
- `tests/test_lai_array_parser.py` 覆盖数组 AST、类型声明、字面量、索引读取和元素修改解析。
- `tests/test_lai_arrays.py` 覆盖数组语义、类型、静态边界、标量复用、作用域和 LLVM `LetStmt` 拒绝。
- `tests/test_lai_array_runtime.py` 使用真实 `clang` 覆盖初始化顺序、索引单次求值、动态边界、短路和名称冲突。

2026-09-05 验证结果：数组语义/真实 `clang` 运行测试 27 项通过，数组 AST/解析测试 23 项通过；完整 `python -m unittest discover -q` 和最终 `python -m unittest discover -v` 均为 449 项通过、无 skip，CLI help 显示 v0.39 且对应测试通过；全部既有 C/LLVM 示例验证通过。逐项 E2E 输出和预期拒绝见 `docs/ai/active-context.md` 的 v0.39 验证记录，不将历史 399 项当作当前总数。

2026-09-07 v0.40 第一阶段验证：最终 `python -m unittest discover -q` 为 480 项通过、无 skip；CLI help v0.40 测试先失败后通过。新示例 `examples/array_element_assignment.ly` 默认 C 与严格 C11 / `-O2` 均输出 `85`、`60`、`10`、`after`、`1`；既有 C/LLVM 示例通过，新示例 LLVM 按预期 exit 1 报第 1 行 `FunctionDef`。详细证据见 `docs/ai/active-context.md`。

## 当前未实现范围

- 隐式数组类型、长度 API、数组遍历、方法、切片和多维数组
- 数组参数/返回、整数组复制/赋值/比较/打印；参数/返回和复制/赋值已列入未编号后续候选，不承诺版本
- `main` 返回类型
- bare `return`、无返回值函数或 `main` 中的 `return`
- 一般常量条件折叠、静态非空 `for` 证明、完整 CFG 或不可达 warning 模式
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- `count++`
- 浮点数、动态整数范围分析、运行时错误恢复、动态非正 `for step` 的恢复/反向循环语义和完整运算符优先级
- 函数重载、闭包和模块系统
- 默认参数、命名参数和可变参数
- 单词关键字 `elseif`
- 字符串相加
- 布尔逻辑符号别名 `&&` / `||` / `!` 和非 `bool` truthiness
- 比较链和字符串排序比较
- 缩进块语法
- 通用标量变量类型注解和完整类型推导；局部显式标注目前只支持上述三种一维数组类型
- 完整 LLVM 语言覆盖：实验性文本 LLVM IR 不支持动态表达式、变量、赋值、比较、`LogicalNotExpr`、`LogicalExpr`、布尔、字符串、控制流或用户函数；共享 checker 在进入后端前拒绝纯静态零除和 i32 中间溢出，LLVM 不接受源码层静态回绕
- 用户可调用标准库、包管理、模块系统
- GC、JIT、并发调度
- AI 自动优化能力

这些属于后续路线，不应在当前文档里描述成已完成。

## 技术栈

- Python 3.12
- Python 标准库 `unittest`
- C 作为完整默认后端输出，实验性 LLVM 文本 IR 不使用 `llvmlite`
- `clang` 作为本机编译器
- Windows 工作目录：`D:\Porject\TestProgrammingLanguage`

## 关键入口

- 示例源文件：`main.ly`
- 编译器：`lai_compiler.py`
- 通用后端描述符：`lai_backend.py`
- AST 模块：`lai_ast.py`
- 局部数组类型模块：`lai_types.py`
- 核心共享模块：`lai_core.py`
- 语义检查模块：`lai_checker.py`
- C 后端模块：`lai_c_backend.py`
- 共享 clang 模块：`lai_clang.py`
- LLVM 后端模块：`lai_llvm_backend.py`
- LLVM 示例：`examples/llvm_minimal.ly`、`examples/llvm_arithmetic.ly`
- C 比较示例：`examples/basic_comparisons.ly`
- C 布尔逻辑示例：`examples/boolean_logic.ly`
- C 运行时整数安全示例：`examples/runtime_integer_safety.ly`
- C 通用函数早退示例：`examples/general_early_return.ly`
- C 局部数组示例：`examples/local_arrays.ly`，实际输出 `95`、`LAI`、`1`，布尔沿用数字打印
- 标准库辅助模块：`lai_stdlib.py`
- 测试：`tests/test_lai_compiler.py`、`tests/test_lai_flow.py`、`tests/test_lai_runtime.py`
- 生成物：`build/main.c`、`build/main.exe`
- 设计文档：`docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
- 实施计划：`docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`
- 当前版本设计：`docs/superpowers/specs/2026-09-07-lai-v0.40-array-element-assignment-design.md`
- 当前版本计划：`docs/superpowers/plans/2026-09-07-lai-v0.40-array-element-assignment.md`
- 上一版本设计：`docs/superpowers/specs/2026-09-05-lai-v0.39-local-arrays-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-09-05-lai-v0.39-local-arrays.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-28-lai-v0.37-runtime-integer-safety-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-28-lai-v0.37-runtime-integer-safety.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-28-lai-v0.35-basic-comparisons-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-28-lai-v0.35-basic-comparisons.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.32-textual-llvm-backend-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-13-lai-v0.32-textual-llvm-backend.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.31-backend-boundary-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-11-lai-v0.31-backend-boundary.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.30-modulo-assign-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-11-lai-v0.30-modulo-assign.md`
- 更早版本设计：`docs/superpowers/specs/2026-07-10-lai-v0.29-modulo-expressions-design.md`
- 更早版本计划：`docs/superpowers/plans/2026-07-10-lai-v0.29-modulo-expressions.md`

## 长期方向

长期设计想让 LAI 成为“语法极简、对 AI 友好、底层可高性能优化”的语言。这个方向记录在
`docs/Document` 下的两份中文文档里。当前实现应逐步靠近这个方向，但每一步都要保持小范围、可测试、可运行。

当前 v0.40 第一阶段已实现局部数组元素修改，checked i32 和早退规则继续有效。LLVM 子集未扩大：完整数组示例在第 1 行报 `FunctionDef`，纯 main 数组单测验证 `LetStmt` 能力错误。长度 API 和遍历仍在 v0.40 待实现，不代表 v0.40 全量完成；v0.41 多维数组不顺延，之后依次为 v0.42 反向循环、v0.43 字符串/最小用户标准库、v0.44 浮点数、v0.45 LLVM 变量模型与语义复盘。v0.40-v0.45 仍有 6 个尚有工作的编号版本。
