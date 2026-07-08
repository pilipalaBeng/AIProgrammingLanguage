# 当前上下文

最后更新：2026-07-08

## 当前工作状态

仓库已经具备 LAI v0.10 的最小可运行编译器：

- `main.ly` 是示例输入。
- `lai_compiler.py` 负责词法、语法、文件编译和 CLI，并兼容导出旧入口。
- `lai_ast.py` 负责 AST 节点定义。
- `lai_core.py` 负责共享错误类型和核心规则。
- `lai_checker.py` 负责语义/类型检查。
- `lai_c_backend.py` 负责生成 C。
- `lai_stdlib.py` 负责内部标准库/运行时 C 输出辅助。
- `tests/test_lai_compiler.py` 覆盖核心翻译行为和错误行为。
- `build/main.c` 与 `build/main.exe` 是生成物。

v0.10 新增了最小 `else` 分支语法。源码现在可以写：

```lai
if ready {
    print("yes")
} else {
    print("no")
}
```

parser 会把 else 分支放进 `IfStmt.else_statements`；checker 和 C backend 分别用独立符号表副本处理 then/else 分支，避免分支内变量互相泄漏。

v0.9 将 `Program`、语句节点和表达式节点拆到 `lai_ast.py`。
parser、checker、C backend 现在共享同一套 AST 节点；`lai_compiler.py` 仍兼容导出这些节点，旧导入路径可继续用。

v0.8 将 `LaiCompileError`、`check_program(program)`、`generate_c(program)` 分别拆到
`lai_core.py`、`lai_checker.py`、`lai_c_backend.py`。`lai_compiler.py` 仍然重新导出这些入口，
所以旧测试和用户脚本不需要改导入路径。

v0.7 新增了 `lai_stdlib.py`。它目前不是用户可直接调用的标准库，而是内部边界：
集中管理 C preamble、字符串转义和 `print` 的 C `printf` 输出格式。

未来数据结构命名已新增草案文档：`docs/ai/data-structures-roadmap.md`。当前倾向为数组使用
C# 风格 `int[]`，字典使用 `dict`，但这些都尚未实现，不能写进当前语言能力。

v0.6 在 `.ly` 源码入口基础上新增了独立的 `check_program(program)` 阶段。
编译器现在会在生成 C 之前检查变量、函数调用、`if` 条件、整数加法和比较表达式的基础类型。
错误信息会尽量说明实际类型，例如 `line 3: comparison operands must both be int, got string and int`。

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

1. 继续加语言最小能力：下一步优先考虑函数参数或返回值，只择一推进。
2. 每新增一个语法点，先补 `tests/test_lai_compiler.py`。
3. 当 `compile_source` 开始变长时，再考虑拆分词法、解析和生成模块。
4. 在切换到 LLVM IR 前，先把 C 后端维持稳定，避免同时换语法和后端。

## 当前风险

- 远期方案文档很宏大，容易把 v0 做过大。
- 当前表达式解析仍然很小，适合 v0，但不适合复杂表达式和完整运算符优先级。
- `build/` 下文件是生成物，手动修改会被下次编译覆盖。
- Windows 下 `clang` 和 MSVC 链接环境可能受终端环境影响。

## 推荐验证命令

```powershell
python -m unittest discover -v
python lai_compiler.py main.ly --run
```

## 2026-07-06 v0.1 Compiler Architecture Update

The compiler has been refactored internally into a structured pipeline:

```text
source -> lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang
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
- Minimal `if` statements with optional `else`.

The control-flow scope remains small: no loops, parentheses, or full operator
precedence yet.

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

## 2026-07-08 v0.6 Type Checker Update

The compiler now has an explicit semantic/type checking stage:

- Public checker entry: `check_program(program)`.
- Expression types currently tracked: `string`, `int`, and `bool`.
- `if` conditions must be `bool`.
- Integer addition operands must be `int`.
- Comparison operands currently must both be `int`.

This version does not add new surface syntax. It makes existing behavior more
explicit before C code generation.

## 2026-07-08 v0.7 Stdlib Boundary Update

The compiler now has a small internal standard-library/runtime helper module:

- New module: `lai_stdlib.py`.
- `c_preamble()` owns generated C preamble lines.
- `escape_c_string()` owns C string literal escaping.
- `c_print_string_literal()` and `c_print_value()` own generated `printf` lines.

This version does not add user-facing standard library calls yet. It creates a
clear place for future runtime helpers instead of keeping all details inside
`lai_compiler.py`.

## 2026-07-08 v0.8 Module Split Update

The compiler now has clearer module boundaries:

- `lai_core.py`: shared `LaiCompileError` and `NAME_RE`.
- `lai_checker.py`: semantic/type checker entry `check_program(program)`.
- `lai_c_backend.py`: C backend entry `generate_c(program)`.
- `lai_compiler.py`: lexer, parser, compile-file flow, CLI, and compatibility re-exports.

This version keeps source syntax unchanged. It prepares the project for future
language features by making checker/backend changes more localized.

## 2026-07-08 v0.9 AST Split Update

The compiler now has a shared AST module:

- `lai_ast.py`: `Program`, statement nodes, and expression nodes.
- `lai_compiler.py`: parser creates `lai_ast` nodes and still re-exports them.
- `lai_checker.py`: uses concrete AST classes instead of node-name strings.
- `lai_c_backend.py`: uses concrete AST classes instead of node-name strings.

This version keeps source syntax unchanged and makes future parser/checker/backend
changes easier to read.

## 2026-07-08 v0.10 Else Update

The compiler now supports optional `else` blocks:

- Lexer recognizes `else`.
- Parser attaches optional else bodies to `IfStmt.else_statements`.
- Checker verifies both then and else branches with separate block-local symbol copies.
- C backend emits `if (...) { ... } else { ... }`.
- The sample `main.ly` prints `else works` through the new branch syntax.

This version does not add `else if`, loops, function parameters, or return values.
