# LAI 项目简报

最后更新：2026-07-06

## 项目一句话

LAI（灵语）是一个面向 AI 时代的极简高性能编程语言实验项目。当前仓库落地的是
v0.2 编译器原型：先做出能从 `.lai` 翻译到 C、再编译运行的最小闭环。

## 当前阶段目标

当前阶段只追求一个可靠的最小版本：

```text
main.lai -> lexer -> parser -> AST -> C codegen -> clang -> build/main.exe
```

这一步的意义不是完成语言本体，而是证明：

- 能定义一个稳定的 LAI 源文件格式。
- 能解析并校验极小语法。
- 能生成可编译的 C 代码。
- 能通过测试和命令行示例验证结果。

## 当前已实现能力

语言层面：

- 程序入口：`fn main() { ... }`
- 单行注释：`// comment`
- 字符串变量：`let name = "LingYu"`
- 整数变量：`let count = 123`
- 整数加法变量：`let count = 1 + 2`
- 打印字面量：`print("Hello LAI")`
- 打印整数字面量和加法表达式：`print(123)`、`print(1 + 2)`
- 打印变量：`print(name)`

编译器层面：

- `compile_source(source: str) -> str`
- `compile_file(source_path: Path, build_dir: Path) -> tuple[Path, Path]`
- 命令行入口：`python lai_compiler.py main.lai --run`
- 行号化错误：缺失 `main`、未知变量、非法变量名、重复变量、非法字符串等
- 生成 C 并调用 `clang`

测试层面：

- `tests/test_lai_compiler.py` 覆盖词法、解析、C 生成、字符串打印、整数变量、整数字面量打印、整数加法、注释、未知变量、非法变量名和缺失入口。

## 明确不在 v0.2 范围内

- 自定义函数
- 条件分支和循环
- 字符串相加
- 变量参与加法表达式
- 括号表达式和完整运算符优先级
- 缩进块语法
- 类型注解和类型推导
- LLVM IR 生成
- 标准库、包管理、模块系统
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

- 示例源文件：`main.lai`
- 编译器：`lai_compiler.py`
- 测试：`tests/test_lai_compiler.py`
- 生成物：`build/main.c`、`build/main.exe`
- 设计文档：`docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
- 实施计划：`docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`

## 长期方向

长期设计想让 LAI 成为“语法极简、对 AI 友好、底层可高性能优化”的语言。这个方向记录在
`docs/Document` 下的两份中文文档里。当前实现应逐步靠近这个方向，但每一步都要保持小范围、可测试、可运行。
