# 当前上下文

最后更新：2026-07-23

## 当前工作状态

仓库已经具备 LAI v0.34 的最小可运行编译器：

- `main.ly` 是示例输入。
- `lai_compiler.py` 负责词法、语法、文件编译和 CLI，并在解析/检查后默认委托 `C_BACKEND`。
- `lai_ast.py` 负责 AST 节点定义。
- `lai_core.py` 负责共享错误类型和核心规则。
- `lai_checker.py` 负责语义/类型检查。
- `lai_backend.py` 负责不可变的通用 `Backend` 描述符。
- `lai_clang.py` 负责共享 `clang` 调用和既有错误措辞。
- `lai_c_backend.py` 负责完整 C 生成、构建和默认 `C_BACKEND`。
- `lai_llvm_backend.py` 负责不依赖 `llvmlite` 的实验性文本 LLVM IR 生成和 `LLVM_BACKEND`。
- `lai_stdlib.py` 负责内部标准库/运行时 C 输出辅助。
- `tests/test_lai_compiler.py` 覆盖核心翻译行为和错误行为。
- `build/main.c` 与 `build/main.exe` 是生成物。

v0.33 没有新增 LAI 源码语法。`compile_source` 和 `compile_file` 默认使用完整 `C_BACKEND`，CLI 提供 `--backend {c,llvm}` 且默认是 `c`。`lai_clang.py` 集中共享 clang 调用和既有错误措辞；`lai_llvm_backend.py` 不依赖 `llvmlite`，可为空 `main` 或顶层 `print` 的 `IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr` 生成文本 LLVM IR。变量、赋值、比较、布尔、字符串、控制流和用户函数仍是明确 LLVM 能力错误；可运行示例是 `examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly`。计算后为零的除数以及 `INT_MIN / -1`、`INT_MIN % -1` 仅由实验性 LLVM lowering 拒绝，默认 C 后端的显式静态零除数边界不变。下一步 v0.34 的前缀一元 `+` / `-` 设计已经用户确认，待编写实施计划与代码；设计文档是 `docs/superpowers/specs/2026-07-23-lai-v0.34-unary-integer-expressions-design.md`。`*`、`/` 和 `%` 仍只支持 `int` 操作数，优先级高于 `+` / `-`，括号仍可覆盖分组；`/` 当前生成 C 整数除法，`%` 当前生成 C 整数余数，结果都为 `int`。源码仍可写：

```lai
fn first_over_two(limit: int) -> int {
    let count = 0
    while count < limit {
        if count > 2 {
            return count
        }
        count += 1
    }
    return limit
}

fn show_for_demo() {
    for j from 0 through 4 step 2 {
        print(j)
    }
}

fn show_group_demo() {
    let grouped = (1 + 2)
    print(grouped)
    if (grouped == 3) {
        print("group works")
    }
}

fn show_subtract_demo() {
    let start = 5
    let result = start - 2
    result -= 1
    print(result)
}

fn show_multiply_demo() {
    let base = 2 + 3 * 4
    print(base)
    let grouped = (2 + 3) * 4
    grouped *= 2
    print(grouped)
}

fn show_division_demo() {
    let divided = 8 / 2
    print(divided)
    let grouped = (6 + 4) / 2
    print(grouped)
    let shrinking = 16
    shrinking /= 2
    print(shrinking)
}

fn show_modulo_demo() {
    let remainder = 7 % 3
    print(remainder)
    let grouped = (10 + 5) % 4
    print(grouped)
    let folded = 29
    folded %= 5
    print(folded)
}

fn show_while_demo() {
    let count = 0
    while count < 3 {
        print(count)
        count += 1
    }
}

fn show_loop_control_demo() {
    let control = 0
    while control < 5 {
        control += 1
        if control < 2 {
            continue
        }
        print(control)
        if control > 2 {
            break
        }
    }
}

fn main() {
    // show_for_demo()
    show_group_demo()
    show_subtract_demo()
    show_multiply_demo()
    show_division_demo()
    show_modulo_demo()
}
```

`show_for_demo()` 保留了 `for j from 0 through 4 step 2` 示例；`through` 包含终点，调用该函数时会依次输出 `0`、`2`、`4`。
`let grouped = (1 + 2)` 会保留括号分组并生成 C `(1 + 2)`；`if (grouped == 3)` 仍按内部比较表达式推断为 `bool`。
`let result = start - 2` 会生成 C `start - 2`，checker 要求减法左右两侧都是 `int`。
`result -= 1` 会生成 C `result = result - 1;`，checker 要求目标和值都是 `int`。
`let base = 2 + 3 * 4` 会按 `*` 高于 `+` 解析并生成 C `2 + 3 * 4`；`let grouped = (2 + 3) * 4` 会保留括号分组。
`grouped *= 2` 会生成 C `grouped = grouped * 2;`，checker 要求目标和值都是 `int`。
`let divided = 8 / 2` 会生成 C `8 / 2`，checker 要求除法左右两侧都是 `int`。显式静态 `8 / 0` 和 `8 / (0)` 会报 `division by zero`，但动态运行时除零检查尚未实现。
`shrinking /= 2` 会生成 C `shrinking = shrinking / 2;`，checker 要求目标和值都是 `int`；显式静态 `count /= 0` 和 `count /= (0)` 会报 `division by zero`。
`let remainder = 7 % 3` 会生成 C `7 % 3`，checker 要求取模左右两侧都是 `int`。显式静态 `7 % 0` 和 `7 % (0)` 会报 `modulo by zero`，但动态运行时取模除零检查尚未实现。
`folded %= 5` 会生成 C `folded = folded % 5;`，checker 要求目标和值都是 `int`；显式静态 `count %= 0` 和 `count %= (0)` 会报 `modulo by zero`。
`for` 的起点、终点和步长必须是 `int`，
显式 `step 0` 会报错。循环变量是循环体局部 `int`，不会泄漏到循环外。
`while` 条件必须是 `bool`。赋值只能写给已有变量或参数，且新值类型必须和原类型一致。
`+=`、`-=`、`*=`、`/=` 和 `%=` 只能用于已有 `int` 变量或参数，右侧表达式也必须是 `int`，生成 C 时分别输出为 `name = name + value;`、`name = name - value;`、`name = name * value;`、`name = name / value;` 和 `name = name % value;`。
`break` / `continue` 只能写在循环体内部。返回值函数的循环体内可以写类型正确的 `return`，
但函数末尾仍需要顶层兜底 `return` 或完整返回分支；`while true { return ... }` 暂不算保证返回路径。
v0.33 仍不支持倒序循环、负数步长、`for item in list`、`count++`、浮点数、动态运行时除零检查、负数、完整运算符优先级、赋值表达式或通用 `return` 早退。实验性 LLVM 后端也不支持变量、赋值、比较、布尔、字符串、控制流或用户函数。

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

1. v0.34 已完成前缀一元 `+` / `-`、i32 静态边界、C/LLVM lowering、可运行示例和发布文档；动态运行时整数溢出与动态非正 step 仍不检查。
2. v0.35 完善基础比较能力；具体运算符集合和类型规则仍需用户单独设计确认。之后再评估布尔逻辑、通用早退和数组闭环。
3. v0.40 重新评估 LLVM 变量模型和 SSA，不预先承诺一个版本追平完整 C 后端。
4. 保持 `--backend {c,llvm}` 默认 `c`，保持完整 C 后端稳定。
5. 每新增一个用户可见语法点，先给出 2-3 个有意义候选、例子、利弊、与 LAI 一致性、成熟语言实践和明确推荐，由用户选择；内部重构不制造虚假语法选项。
6. 当 `compile_source` 开始变长时，再考虑拆分词法、解析和生成模块。

## 当前风险

- 远期方案文档很宏大，容易把 v0 做过大。
- 当前表达式解析仍然很小，适合 v0，但不支持完整运算符优先级。
- `build/` 下文件是生成物，手动修改会被下次编译覆盖。
- Windows 下 `clang` 和 MSVC 链接环境可能受终端环境影响。

## 推荐验证命令

```powershell
python -m unittest discover -v
python lai_compiler.py main.ly --run
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
python lai_compiler.py examples/unary_integer.ly --run
python lai_compiler.py examples/unary_integer.ly --backend llvm --run
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

## 2026-07-09 v0.18 For Loop Update

The compiler now supports a minimal counted `for` loop:

- Syntax: `for i from 0 to 3 { ... }`.
- `to` excludes the end value, so `0 to 3` iterates `0`, `1`, `2`.
- The loop variable is a local `int` visible only inside the loop body.
- `start` and `end` must both be `int` expressions.
- `break`, `continue`, nested loops, and loop-local `return` work inside `for`.
- C backend emits `for (int i = start; i < end; i = i + 1)`.

This version does not add `step`, reverse loops, inclusive-end loops, `for item in list`, `++`, `+=`, general early return, or LLVM IR.

## 2026-07-09 v0.19 Plus Assignment Update

The compiler now supports minimal `+=` assignment sugar:

- Syntax: `count += 1`.
- Semantics: `name += expr` is checked as an existing `int` target plus an `int` value.
- C backend emits `name = name + value;`.
- `+=` works in functions, `while`, `for`, and branches.

This version does not add `-=`, `*=`, `/=`, `++`, ordinary subtraction, negative integers, parentheses, operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.20 For Step Update

The compiler now supports optional positive forward step values in counted `for` loops:

- Syntax: `for i from 0 to 6 step 2 { ... }`.
- `to` still excludes the end value, so `0 to 6 step 2` iterates `0`, `2`, `4`.
- Omitted `step` still defaults to `1`.
- `start`, `end`, and `step` must be `int`.
- Explicit static `step 0` is rejected.
- C backend emits `for (int i = start; i < end; i = i + step)`.

This version does not add reverse loops, inclusive-end loops, `for item in list`, negative integers, parentheses, operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.21 Through Loop Update

The compiler now supports inclusive-end counted loops:

- Syntax: `for i from 0 through 3 { ... }`.
- `through` includes the end value, so `0 through 3` iterates `0`, `1`, `2`, `3`.
- `to` remains exclusive and existing `for i from 0 to 3` behavior is unchanged.
- `through` can combine with `step`, such as `for i from 0 through 6 step 2`.
- `through` is now a reserved keyword and cannot be used as a variable name.
- C backend emits `for (int i = start; i <= end; i = i + step)` for `through`.

This version does not add reverse loops, negative steps, `for item in list`, negative integers, parentheses, operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.22 Parenthesized Expressions Update

The compiler now supports parenthesized expressions:

- Syntax: `let count = (1 + 2)` and `print((1 + 2))`.
- Parentheses preserve grouping through `GroupExpr` in the shared AST.
- Checker infers a grouped expression from its inner expression type.
- C backend keeps grouping by emitting parenthesized C such as `(1 + 2)`.
- Parentheses can be used in `let`, `print`, `return`, call arguments, assignments, conditions, and `for` expressions.
- Empty parentheses and unclosed parentheses are rejected.

This version does not add ordinary subtraction, multiplication, division, negative integers, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.23 Subtraction Expressions Update

The compiler now supports ordinary integer subtraction expressions:

- Syntax: `let count = 5 - 2`, `print(5 - 2)`, and `return a - b`.
- Subtraction is represented by `SubtractExpr(left, right)` in the shared AST.
- Parser treats `+` and `-` as the same left-associative expression layer.
- Checker requires both subtraction operands to be `int`.
- C backend emits readable C such as `count - 1`.
- `count -= 1` is still rejected, now with an explicit unsupported assignment-operator error.

This version does not add `-=`, negative integers, multiplication, division, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.24 Minus Assignment Update

The compiler now supports minimal `-=` assignment sugar:

- Syntax: `count -= 1` and `count -= add(1, 2)`.
- Semantics: `name -= expr` is checked as an existing `int` target minus an `int` value.
- The shared AST represents this as `MinusAssignStmt(name, value, line)`.
- C backend emits readable C such as `count = count - 1;`.
- `-=` works in functions, `while`, `for`, and branches.

This version does not add `*=`, `/=`, `count++`, negative integers, multiplication, division, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.25 Multiplication Expressions Update

The compiler now supports ordinary integer multiplication expressions:

- Syntax: `let count = 2 * 3`, `print(2 * 3)`, and `return a * b`.
- Multiplication is represented by `MultiplyExpr(factors)` in the shared AST.
- Parser now has a minimal arithmetic precedence split: `*` binds tighter than `+` and `-`.
- Parentheses continue to override grouping, such as `(2 + 3) * 4`.
- Checker requires all multiplication factors to be `int`.
- C backend emits readable C such as `2 + 3 * 4`.

This version does not add `*=`, `/`, `/=`, `%`, negative integers, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.26 Multiply Assignment Update

The compiler now supports minimal integer `*=` assignment sugar:

- Syntax: `count *= 2` and `count *= add(1, 2)`.
- Semantics: `name *= expr` is checked as an existing `int` target multiplied by an `int` value.
- The shared AST represents this as `MultiplyAssignStmt(name, value, line)`.
- C backend emits readable C such as `count = count * 2;`.
- `*=` works in functions, `while`, `for`, and branches.

This version does not add `/`, `/=`, `%`, `count++`, negative integers, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.27 Division Expressions Update

The compiler now supports ordinary integer division expressions:

- Syntax: `let count = 8 / 2`, `print(8 / 2)`, and `return a / b`.
- Division is represented by `DivideExpr(left, right)` in the shared AST.
- Parser treats `/` at the same precedence level as `*`; both bind tighter than `+` and `-`.
- Parentheses continue to override grouping, such as `(6 + 4) / 2`.
- Checker requires both division operands to be `int` and rejects static zero denominators such as `8 / 0` and `8 / (0)`.
- C backend emits readable C such as `8 + 6 / 2`.

This version does not add `/=`, `%`, floating-point numbers, negative integers, dynamic runtime division-by-zero checks, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.28 Divide Assignment Update

The compiler now supports integer divide assignment statements:

- `count /= 2`
- `count /= half(8)`
- `count /= (6 / 2)`

The shared AST represents this as `DivideAssignStmt(name, value, line)`. The parser tokenizes `/=` as `SLASH_EQUAL` after preserving `//` comments. Checker and C backend require an existing `int` target and an `int` value, reject static zero values such as `count /= 0` and `count /= (0)`, and emit C as `name = name / value;`.

This version does not add `%`, `%=`, floating-point numbers, negative integers, dynamic runtime division-by-zero checks, full operator precedence, general early return, or LLVM IR.

## 2026-07-10 v0.29 Modulo Expressions Update

The compiler now supports ordinary integer modulo expressions:

- `let remainder = 7 % 3`
- `print(8 + 7 % 3)`
- `return value % 2`
- `let grouped = (10 + 5) % 4`

Modulo is represented by `ModuloExpr(left, right)` in the shared AST. The parser treats `%` at the same precedence level as `*` and `/`; all three bind tighter than `+` and `-`. Checker requires both operands to be `int` and rejects static zero right-hand values such as `7 % 0` and `7 % (0)` with `modulo by zero`. The C backend emits readable C such as `7 % 3`.

This version does not add `%=`, floating-point numbers, negative integers, dynamic runtime modulo-by-zero checks, full operator precedence, general early return, or LLVM IR.

## 2026-07-11 v0.30 Modulo Assignment Update

The compiler now supports `%=` modulo assignment statements:

- `count %= 3`
- `count %= remainder(12)`
- `count %= (10 % 4)`

Modulo assignment is represented by `ModuloAssignStmt(name, value, line)` in the
shared AST. The tokenizer recognizes `%=` as `PERCENT_EQUAL` before ordinary
`%`, and the parser treats it as a statement-level compound assignment, not an
expression. Checker requires an existing `int` target and an `int` RHS, rejects
static zero values such as `count %= 0` and `count %= (0)` with `modulo by
zero`, and the C backend emits `name = name % value;`.

This version does not add `count++`, floating-point numbers, negative integers,
dynamic runtime modulo-by-zero checks, assignment expressions, full operator
precedence, general early return, or LLVM IR.
