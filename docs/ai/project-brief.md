# LAI 项目简报

最后更新：2026-07-09

## 项目一句话

LAI（灵语）是一个面向 AI 时代的极简高性能编程语言实验项目。当前仓库落地的是
v0.15 编译器原型：先做出能从 `.ly` 翻译到 C、再编译运行的最小闭环。

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
- 正式源码扩展名：`.ly`
- 单行注释：`// comment`
- 字符串变量：`let name = "LingYu"`
- 整数变量：`let count = 123`
- 整数加法变量：`let count = 1 + 2`
- 布尔变量：`let ready = true`
- 比较表达式变量：`let ok = count == 3`
- 打印字面量：`print("Hello LAI")`
- 打印整数字面量和加法表达式：`print(123)`、`print(1 + 2)`
- 打印布尔值和比较结果：`print(true)`、`print(1 < 2)`
- 打印变量：`print(name)`
- 条件语句：`if ready { ... }`、`if is_ready(count) { ... }`、`if 1 < 2 { ... }`、`if false { ... } else { ... }`、`if false { ... } else if true { ... } else { ... }`

编译器层面：

- `compile_source(source: str) -> str`
- `check_program(program: Program) -> None`
- `compile_file(source_path: Path, build_dir: Path) -> tuple[Path, Path]`
- `lai_ast.py` 集中定义 AST 节点
- `lai_core.py` 共享错误类型和核心名称规则
- `lai_checker.py` 承载语义/类型检查
- `lai_c_backend.py` 承载 C 后端
- `lai_stdlib.py` 内部管理 C preamble、字符串转义和 `print` 输出格式
- 命令行入口：`python lai_compiler.py main.ly --run`
- 行号化错误：缺失 `main`、未知变量、未知函数、非法变量名、重复变量、非法字符串、非布尔 `if` 条件、非整数加法/比较、参数错误、返回值错误等
- 生成 C 并调用 `clang`

测试层面：

- `tests/test_lai_compiler.py` 覆盖词法、解析、语义/类型检查、C 生成、字符串打印、整数变量、整数字面量打印、整数加法、注释、布尔值、比较表达式、`if`、`else`、`else if`、`while`、赋值、用户函数、函数参数、函数返回值、分支返回控制流、函数调用表达式、未知变量、未知函数、非法变量名和缺失入口。
- `tests/test_lai_ast.py` 覆盖共享 AST 节点、`else` 分支节点、`else if` 嵌套节点、`ReturnStmt`、`CallExpr`、`AssignStmt`、`WhileStmt` 和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖内部标准库/运行时 C 输出辅助模块。

## 明确不在 v0.15 范围内

- `main` 返回类型
- `return` 早退
- 循环中的 `return` 控制流分析
- `break` / `continue`
- `for`
- `count++` 和 `count += 1`
- 函数重载、闭包和模块系统
- 默认参数、命名参数和可变参数
- 单词关键字 `elseif`
- 字符串相加
- 括号表达式和完整运算符优先级
- 缩进块语法
- 变量类型注解和完整类型推导
- LLVM IR 生成
- 用户可调用标准库、包管理、模块系统
- GC、JIT、并发调度
- AI 自动优化能力

这些属于后续路线，不应在当前文档里描述成已完成。

## 技术栈

- Python 3.12
- Python 标准库 `unittest`
- C 作为临时后端输出
- `clang` 作为本机编译器
- Windows 工作目录：`D:\Porject\TestProgrammingLanguage`

## 关键入口

- 示例源文件：`main.ly`
- 编译器：`lai_compiler.py`
- AST 模块：`lai_ast.py`
- 核心共享模块：`lai_core.py`
- 语义检查模块：`lai_checker.py`
- C 后端模块：`lai_c_backend.py`
- 标准库辅助模块：`lai_stdlib.py`
- 测试：`tests/test_lai_compiler.py`
- 生成物：`build/main.c`、`build/main.exe`
- 设计文档：`docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
- 实施计划：`docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`
- 当前版本设计：`docs/superpowers/specs/2026-07-09-lai-v0.15-while-assignment-design.md`
- 当前版本计划：`docs/superpowers/plans/2026-07-09-lai-v0.15-while-assignment.md`
- 上一版本设计：`docs/superpowers/specs/2026-07-09-lai-v0.14-branch-return-flow-design.md`
- 上一版本计划：`docs/superpowers/plans/2026-07-09-lai-v0.14-branch-return-flow.md`

## 长期方向

长期设计想让 LAI 成为“语法极简、对 AI 友好、底层可高性能优化”的语言。这个方向记录在
`docs/Document` 下的两份中文文档里。当前实现应逐步靠近这个方向，但每一步都要保持小范围、可测试、可运行。
