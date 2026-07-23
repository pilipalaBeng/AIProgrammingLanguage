# LAI 项目简报

最后更新：2026-07-23

## 项目一句话

LAI（灵语）是一个面向 AI 时代的极简高性能编程语言实验项目。当前仓库落地的是
v0.34 编译器原型：先做出能从 `.ly` 翻译到 C、再编译运行的完整默认闭环，同时加入受限的实验性文本 LLVM IR 后端。

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

- 程序入口：`fn main() { ... }`
- 用户函数：`fn greet() { ... }`
- 带参数用户函数：`fn show(name: string, count: int, ready: bool) { ... }`
- 带返回值用户函数：`fn add(a: int, b: int) -> int { return a + b }`
- 返回值函数可用完整 `if / else if / else` 分支返回
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
- 返回值函数中的循环体局部返回：`while count < limit { if count > 2 { return count } }`
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
- `lai_core.py` 共享错误类型和核心名称规则
- `lai_checker.py` 承载语义/类型检查
- `lai_backend.py` 承载不可变的通用 `Backend` 描述符
- `lai_clang.py` 承载共享 `clang` 调用和既有错误措辞
- `lai_c_backend.py` 承载完整 C 源码生成、构建和默认 `C_BACKEND`
- `lai_llvm_backend.py` 承载不依赖 `llvmlite` 的实验性文本 LLVM IR 生成和 `LLVM_BACKEND`
- `lai_stdlib.py` 内部管理 C preamble、字符串转义和 `print` 输出格式
- 命令行入口：`python lai_compiler.py main.ly --run`
- `--backend {c,llvm}` 固定后端选择，默认 `c`；`examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly` 是可运行 LLVM 示例
- LLVM 支持空 `main` 或顶层 `print` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；范围外的有效 LAI 会报明确能力错误
- 行号化错误：缺失 `main`、未知变量、未知函数、非法变量名、重复变量、非法字符串、非布尔 `if` 条件、非整数加法/比较、参数错误、返回值错误等
- 生成 C 并调用 `clang`
- 默认编译流程解析和检查后委托 `C_BACKEND`；内部测试和未来后端可注入 `Backend`

测试层面：

- `tests/test_lai_compiler.py` 覆盖词法、解析、语义/类型检查、C 生成、字符串打印、整数变量、整数字面量打印、整数加法、整数减法、整数乘法、整数除法、整数取模、最小算术优先级、括号表达式、注释、布尔值、比较表达式、`if`、`else`、`else if`、`while`、`for`、`for step`、`for through`、赋值、`+=`、`-=`、`*=`、`/=`、`%=`、`break`、`continue`、用户函数、函数参数、函数返回值、分支返回控制流、循环体内局部返回、函数调用表达式、未知变量、未知函数、非法变量名和缺失入口。
- `tests/test_lai_ast.py` 覆盖共享 AST 节点、`else` 分支节点、`else if` 嵌套节点、`ReturnStmt`、`CallExpr`、`GroupExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`AssignStmt`、`MinusAssignStmt`、`MultiplyAssignStmt`、`DivideAssignStmt`、`ModuloAssignStmt`、`WhileStmt`、`ForStmt`、`BreakStmt`、`ContinueStmt` 和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖内部标准库/运行时 C 输出辅助模块。
- `tests/test_lai_clang.py` 覆盖共享 clang 调用和错误行为。
- `tests/test_lai_llvm_backend.py` 覆盖实验性 LLVM 文本 IR 的生成、能力错误和整数范围。

## 明确不在 v0.34 完整 LLVM 范围内

- `main` 返回类型
- 通用 `return` 早退，例如循环外的非最终 `if { return ... }`
- `while true { return ... }` 作为保证返回路径
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- `count++`
- 浮点数、动态运行时除零检查、动态整数溢出检查、动态非正 `for step` 检查和完整运算符优先级
- 函数重载、闭包和模块系统
- 默认参数、命名参数和可变参数
- 单词关键字 `elseif`
- 字符串相加
- 完整运算符优先级
- 缩进块语法
- 变量类型注解和完整类型推导
- 完整 LLVM 语言覆盖：实验性文本 LLVM IR 不支持变量、赋值、比较、布尔、字符串、控制流或用户函数；checker 与 C 后端拒绝静态可求值为零的除数，LLVM lowering 还拒绝 i32 回绕后计算为零的除数及 `INT_MIN / -1`、`INT_MIN % -1`
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
- 核心共享模块：`lai_core.py`
- 语义检查模块：`lai_checker.py`
- C 后端模块：`lai_c_backend.py`
- 共享 clang 模块：`lai_clang.py`
- LLVM 后端模块：`lai_llvm_backend.py`
- LLVM 示例：`examples/llvm_minimal.ly`、`examples/llvm_arithmetic.ly`
- 标准库辅助模块：`lai_stdlib.py`
- 测试：`tests/test_lai_compiler.py`
- 生成物：`build/main.c`、`build/main.exe`
- 设计文档：`docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
- 实施计划：`docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`
- 当前版本设计：`docs/superpowers/specs/2026-07-23-lai-v0.34-unary-integer-expressions-design.md`
- 当前版本计划：`docs/superpowers/plans/2026-07-23-lai-v0.34-unary-integer-expressions.md`
- 上一版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.32-textual-llvm-backend-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-07-13-lai-v0.32-textual-llvm-backend.md`
- 上一版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.31-backend-boundary-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-07-11-lai-v0.31-backend-boundary.md`
- 上一版本设计：`docs/superpowers/specs/2026-07-11-lai-v0.30-modulo-assign-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-07-11-lai-v0.30-modulo-assign.md`
- 上一版本设计：`docs/superpowers/specs/2026-07-10-lai-v0.29-modulo-expressions-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-07-10-lai-v0.29-modulo-expressions.md`

## 长期方向

长期设计想让 LAI 成为“语法极简、对 AI 友好、底层可高性能优化”的语言。这个方向记录在
`docs/Document` 下的两份中文文档里。当前实现应逐步靠近这个方向，但每一步都要保持小范围、可测试、可运行。

v0.34 已完成：前缀 `+expr` / `-expr` 使用 `UnaryExpr`，优先级位于分组/基础表达式之后、乘除取模之前；源码 `int` 范围为 `-2147483648..2147483647`，静态拒绝零除数、一元 `INT_MIN` 溢出和 `for step <= 0`。动态运行时溢出和动态非正 step 仍未检查。LLVM 仅在原有顶层整数 `print` 子集中加入 unary，变量、赋值、比较、布尔、字符串、控制流和用户函数仍不支持。下一步是 v0.35 完善基础比较能力，具体语法集合仍需用户选择。
