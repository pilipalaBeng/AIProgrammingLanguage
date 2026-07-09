# 当前上下文

最后更新：2026-07-09

## 当前工作状态

仓库已经具备 LAI v0.17 的最小可运行编译器：

- `main.ly` 是示例输入。
- `lai_compiler.py` 负责词法、语法、文件编译和 CLI，并兼容导出旧入口。
- `lai_ast.py` 负责 AST 节点定义。
- `lai_core.py` 负责共享错误类型和核心规则。
- `lai_checker.py` 负责语义/类型检查。
- `lai_c_backend.py` 负责生成 C。
- `lai_stdlib.py` 负责内部标准库/运行时 C 输出辅助。
- `tests/test_lai_compiler.py` 覆盖核心翻译行为和错误行为。
- `build/main.c` 与 `build/main.exe` 是生成物。

v0.17 在 `break` / `continue` 基础上，新增了返回值函数中循环体内的局部 `return` 检查。源码现在可以写：

```lai
fn first_over_two(limit: int) -> int {
    let count = 0
    while count < limit {
        if count > 2 {
            return count
        }
        count = count + 1
    }
    return limit
}

fn main() {
    let count = 0
    while count < 3 {
        print(count)
        count = count + 1
    }
    let control = 0
    while control < 5 {
        control = control + 1
        if control < 2 {
            continue
        }
        print(control)
        if control > 2 {
            break
        }
    }
}
```

`while` 条件必须是 `bool`。赋值只能写给已有变量或参数，且新值类型必须和原类型一致。
`break` / `continue` 只能写在循环体内部。返回值函数的循环体内可以写类型正确的 `return`，
但函数末尾仍需要顶层兜底 `return` 或完整返回分支；`while true { return ... }` 暂不算保证返回路径。
v0.17 仍不支持 `for`、`count++`、`count += 1` 或通用 `return` 早退。

v0.14 新增了分支 `return` 控制流。带返回值函数现在可以通过完整
`if / else if / else` 保证所有路径返回：

```lai
fn grade(score: int) -> string {
    if score > 90 {
        return "A"
    } else if score > 80 {
        return "B"
    } else {
        return "C"
    }
}
```

返回值函数仍然不支持通用早退；v0.17 只允许循环体内局部 `return`，不做复杂不可达代码分析。

v0.13 新增了函数返回值和函数调用表达式。源码现在可以写：

```lai
fn add(a: int, b: int) -> int {
    return a + b
}

fn is_ready(count: int) -> bool {
    return count == 7
}

fn main() {
    let total = add(3, 4)
    print(total)
    if is_ready(total) {
        print("ok")
    }
}
```

返回类型当前只支持 `string`、`int`、`bool`。`main` 仍然必须写成 `fn main() { ... }`，
不能带参数或返回类型。v0.14 允许带返回值函数用最后顶层 `return expr` 或完整分支返回。

v0.12 新增了用户函数参数。源码现在可以写：

```lai
fn show(name: string, count: int, ready: bool) {
    print(name)
    print(count)
    print(ready)
}

fn main() {
    show("JD", 3, true)
}
```

参数类型当前只支持 `string`、`int`、`bool`。`main` 仍然必须写成 `fn main() { ... }`，
不允许带参数。

v0.11 新增了 `else if` 链式分支语法。源码可以写：

```lai
if score > 90 {
    print("A")
} else if score > 80 {
    print("B")
} else {
    print("C")
}
```

parser 不新增 `ElseIfStmt`，而是把 `else if` 表示成 else 分支里的嵌套 `IfStmt`。
单词关键字 `elseif` 当前不支持。

v0.10 新增了最小 `else` 分支语法。源码可以写 `if ready { ... } else { ... }`。
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

1. 继续加语言最小能力：下一步优先考虑 `for` 循环设计。
2. 每新增一个语法点，先补 `tests/test_lai_compiler.py`。
3. 当 `compile_source` 开始变长时，再考虑拆分词法、解析和生成模块。
4. 在切换到 LLVM IR 前，先把 C 后端维持稳定，避免同时换语法和后端。

## 当前风险

- 远期方案文档很宏大，容易把 v0 做过大。
- 当前表达式解析仍然很小，适合 v0，但不支持括号表达式和完整运算符优先级。
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

## 2026-07-08 v0.11 Else If Update

The compiler now supports `else if` chains:

- Parser recognizes `else if` as two keywords, not one `elseif` keyword.
- `else if` is represented as a nested `IfStmt` inside `IfStmt.else_statements`.
- Existing checker/backend logic handles the nested branch without new AST nodes.
- Tests cover single `else if`, multi-branch chains, AST nesting, and non-bool `else if` conditions.
- The sample `main.ly` prints `else if works`.

This version does not add loops, function parameters, return values, or the single-word `elseif` keyword.

## 2026-07-08 v0.12 Function Parameters Update

The compiler now supports typed user-function parameters:

- Function definitions can declare `string`, `int`, and `bool` parameters.
- Function calls can pass string, integer, boolean, variable, addition, or comparison expressions as arguments.
- The checker validates parameter names, parameter types, argument count, and argument types.
- Function bodies start with parameters in their local symbol table.
- C backend emits parameterized `static void` prototypes, definitions, and calls.
- `fn main(...)` remains unsupported; `main` must be parameterless.

This version does not add return values, `return`, default arguments, named arguments, varargs, overloads, or function-call expressions.

## 2026-07-08 v0.13 Function Returns Update

The compiler now supports typed user-function return values:

- Function definitions can declare return types with `-> string`, `-> int`, or `-> bool`.
- Returning functions must end with a top-level `return expr`.
- Function calls can now be used as expressions in `let`, `print`, `return`, call arguments, and `if` conditions.
- Integer addition can now use integer names and returned integer call expressions, such as `a + b`.
- C backend emits typed `static` prototypes and definitions, such as `static int add(...)`.
- `fn main() -> ...` remains unsupported; `main` must be parameterless and returnless.

This version does not add early return, branch return analysis, recursion-specific behavior, overloads, loops, or parentheses.

## 2026-07-09 v0.14 Branch Return Flow Update

The compiler now supports full branch return paths in returning functions:

- Returning functions may end with `if / else if / else` where every path returns.
- Branch return expressions are type-checked against the declared return type.
- Branch-local symbols still use copied symbol tables.
- `return` after which the same block continues is still rejected.
- No-return-value functions and `main` still reject `return`.

This version does not add general early return, loops, `break`, `continue`, or loop return analysis.

## 2026-07-09 v0.15 While And Assignment Update

The compiler now supports minimal loops and assignment:

- `while condition { ... }`.
- Assignment to existing variables or parameters, such as `count = count + 1`.
- `while` conditions must be `bool`.
- Assignment keeps the original variable type.
- Loop-local `let` variables do not leak outside the loop body.
- C backend emits `while (...) { ... }` and `name = value;`.

This version does not add `break`, `continue`, `for`, `++`, `+=`, or loop return analysis.

## 2026-07-09 v0.16 Break And Continue Update

The compiler now supports loop-control statements:

- `break` exits the nearest `while` loop.
- `continue` skips to the next iteration of the nearest `while` loop.
- `break` / `continue` are valid inside nested `if / else if / else` branches when those branches are inside a loop.
- The checker tracks loop nesting with `loop_depth` and rejects `break` / `continue` outside loops.
- C backend emits `break;` and `continue;`.

This version does not add `for`, labeled loop jumps, `++`, `+=`, or loop return analysis.

## 2026-07-09 v0.17 Loop Return Flow Update

The compiler now allows local `return` statements inside `while` loop bodies in returning functions:

- Loop-body `return expr` is type-checked against the function return type.
- A `return` inside the same loop block must still be the final statement of that block.
- Returning functions still need a final top-level `return` or full final `if / else if / else` return path after the loop.
- `while true { return ... }` is not treated as a guaranteed function return path yet.

This version does not add `for`, `++`, `+=`, general early return, unreachable-code analysis, or LLVM IR.
