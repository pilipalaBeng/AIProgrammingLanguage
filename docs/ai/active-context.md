# 当前上下文

最后更新：2026-07-07

## 当前工作状态

仓库已经具备 LAI v0.5 的最小可运行编译器：

- `main.ly` 是示例输入。
- `lai_compiler.py` 负责解析、校验、生成 C、调用 `clang`。
- `tests/test_lai_compiler.py` 覆盖核心翻译行为和错误行为。
- `build/main.c` 与 `build/main.exe` 是生成物。

本轮将正式源码扩展名从 `.lai` 切换为 `.ly`，示例命令更新为
`python lai_compiler.py main.ly --run`。旧 `.lai` 文件暂时仍可作为普通输入文件被读取，
但文档和示例都以 `.ly` 为准。

v0.4 新增了零参数、无返回值的用户自定义函数。源码现在可以写多个顶层 `fn`，
其中必须包含 `fn main() { ... }`；用户函数会生成 C 的 `static void` 函数，
`main` 或其他用户函数可以通过 `greet()` 形式调用它们。

v0.3 已支持布尔值、基础比较表达式和最小 `if` 语句。`let` 支持字符串、整数、
整数加法、布尔值和比较表达式；`if` 条件支持布尔变量和比较表达式。

本轮文档工作补齐了原本为空的 `AGENTS.md` 和 `docs/ai` 项目记忆文件，方便后续 agent
快速接手。

## 最近的重要事实

- 工作目录是 git 仓库，当前分支为 `main`。
- `docs/ai` 下的项目记忆文件原本都是空文件。
- 原有决策文件名 `0001-auth-design.md` 像模板残留，和当前编译器项目不匹配。
- 当前 v0 仍使用英文关键字和 `{}` 块语法；远期中文名“灵语”不等于当前要使用中文关键字。

## 下一步优先级

建议按这个顺序推进：

1. 继续加语言最小能力：下一步优先考虑基础类型检查/错误提示、`else` 或变量参与加法，只择一推进。
2. 每新增一个语法点，先补 `tests/test_lai_compiler.py`。
3. 当 `compile_source` 开始变长时，再考虑拆分词法、解析和生成模块。
4. 在切换到 LLVM IR 前，先把 C 后端维持稳定，避免同时换语法和后端。

## 当前风险

- 远期方案文档很宏大，容易把 v0 做过大。
- 当前解析是行导向正则解析，适合 v0，但不适合复杂表达式。
- `build/` 下文件是生成物，手动修改会被下次编译覆盖。
- Windows 下 `clang` 和 MSVC 链接环境可能受终端环境影响。

## 推荐验证命令

```powershell
python -m unittest tests.test_lai_compiler -v
python lai_compiler.py main.ly --run
```

## 2026-07-06 v0.1 Compiler Architecture Update

The compiler has been refactored internally into a structured pipeline:

```text
source -> lexer -> parser -> AST -> C codegen -> clang
```

The public CLI and v0 language behavior remain stable. Future syntax work
should extend the lexer, parser, AST nodes, and C code generator in that order,
with tests added before implementation.

## 2026-07-06 v0.2 Language Update

The compiler now supports:

- `// comment` line comments.
- Integer addition expressions such as `print(1 + 2)` and `let count = 1 + 2`.

The expression scope is intentionally small: no parentheses, operator precedence,
string addition, or variable participation inside addition expressions yet.

## 2026-07-06 v0.3 Language Update

The compiler now supports:

- Boolean literals: `true` and `false`.
- Integer comparison expressions: `<`, `>`, and `==`.
- Minimal `if` statements without `else`.

The control-flow scope remains small: no `else`, loops, parentheses, or full
operator precedence yet.

## 2026-07-07 v0.4 Language Update

The compiler now supports:

- Zero-argument user-defined functions such as `fn greet() { ... }`.
- Function call statements such as `greet()`.
- Calls from `main` and from other user-defined functions.

The function scope remains small: no parameters, return values, overloads,
closures, modules, or function calls as expressions yet.

## 2026-07-07 v0.5 Extension Update

The official source file extension is now `.ly`.

- Main example file: `main.ly`.
- Preferred command: `python lai_compiler.py main.ly --run`.
- Old `.lai` files are not rejected by the compiler yet, but should be treated
  as historical/legacy examples.
