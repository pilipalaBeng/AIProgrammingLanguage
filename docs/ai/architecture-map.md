# 架构地图

最后更新：2026-07-13

## 当前架构总览

```text
LAI source (.ly)
    |
    v
compile_source(source)
    |
    +-- tokenize source, skipping // comments
    +-- parse top-level fn blocks into AST
    +-- check symbols and basic expression types
    +-- select C_BACKEND or LLVM_BACKEND (--backend defaults to c)
    |
    v
generated C or textual LLVM IR
    |
    v
clang
    |
    v
native .exe
```

当前架构仍保持单 CLI 入口。v0.33 默认走完整 C 路径，并通过 `--backend {c,llvm}` 提供实验性 LLVM 文本 IR 路径；后端特定的发射和构建不耦合在编译器入口。LLVM 后端不使用 `llvmlite`，支持空 `main` 或顶层 `print` 中的 `IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；变量、赋值、比较、布尔、字符串、控制流和用户函数会报明确能力错误。`examples/llvm_minimal.ly` 与 `examples/llvm_arithmetic.ly` 是可运行示例。

## 文件职责

### `main.ly`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `lai_compiler.py`

v0.33 编译器入口，包含：

- `LaiCompileError`：编译错误类型。
- `Token` 与 `tokenize`：词法分析，支持关键字、标识符、字符串、整数、`+`、`+=`、`-`、`-=`, `*`、`*=`、`/`、`/=`、`%`、`%=`、`<`、`>`、`==`、`:`、`,`、`->`、`step`、`through` 和 `//` 注释。
- `Program`、`Param`、`FunctionDef`、`LetStmt`、`AssignStmt`、`PlusAssignStmt`、`MinusAssignStmt`、`MultiplyAssignStmt`、`DivideAssignStmt`、`ModuloAssignStmt`、`PrintStmt`、`IfStmt`、`WhileStmt`、`ForStmt`、`BreakStmt`、`ContinueStmt`、`CallStmt`、`ReturnStmt`、`StringExpr`、`IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`、`CallExpr`：从 `lai_ast.py` 兼容导出的 AST 节点。
- `parse_source`：把 LAI 源码解析成 AST。
- `check_program`：从 `lai_checker.py` 兼容导出的语义和基础类型检查入口。
- `generate_c`：从 `lai_c_backend.py` 兼容导出的 C 后端入口。
- `compile_source`：解析、检查后通过默认 `C_BACKEND` 将 LAI 源码字符串翻译成 C 源码字符串；可注入 `Backend` 用于内部测试和后端选择。
- `compile_file`：读取 `.ly` 文件，委托指定后端写出生成物并构建。
- `main`：命令行入口，提供默认 `c` 的 `--backend {c,llvm}`。

### `lai_ast.py`

AST 节点模块，包含：

- `Program`：程序根节点。
- `Param`：函数参数节点，保存参数名、参数类型和声明行号。
- `FunctionDef`：用户函数定义，`params` 保存函数参数列表，`return_type` 保存可选返回类型。
- `LetStmt`、`AssignStmt`、`PlusAssignStmt`、`MinusAssignStmt`、`MultiplyAssignStmt`、`DivideAssignStmt`、`ModuloAssignStmt`、`PrintStmt`、`IfStmt`、`WhileStmt`、`ForStmt`、`BreakStmt`、`ContinueStmt`、`CallStmt`、`ReturnStmt`：语句节点，其中 `PlusAssignStmt` 表示 `name += expr`，`MinusAssignStmt` 表示 `name -= expr`，`MultiplyAssignStmt` 表示 `name *= expr`，`DivideAssignStmt` 表示 `name /= expr`，`ModuloAssignStmt` 表示 `name %= expr`；`IfStmt.else_statements` 保存可选 else 分支；`else if` 表示为 else 分支里的嵌套 `IfStmt`；`WhileStmt.statements` 保存循环体；`ForStmt` 保存循环变量、起点、终点、可选步长、是否包含终点和循环体；`BreakStmt` 和 `ContinueStmt` 保存循环控制语句行号；`CallStmt.args` 保存函数调用实参。
- `StringExpr`、`IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`、`CallExpr`：表达式节点，其中 `SubtractExpr` 表示二元减法，`MultiplyExpr` 表示一个或多个乘法因子，`DivideExpr` 表示二元除法，`ModuloExpr` 表示二元取模，`GroupExpr` 保留括号表达式的分组。

### `lai_core.py`

核心共享模块，包含：

- `LaiCompileError`：编译错误类型。
- `NAME_RE`：函数名和变量名的基础规则。

### `lai_checker.py`

语义和基础类型检查模块，包含：

- `check_program`：检查整个 AST。
- `collect_function_names`：收集并校验用户函数名。
- `collect_function_signatures`：收集并校验用户函数签名，用于调用参数数量、参数类型和返回类型检查。
- `FunctionSignature`：记录参数类型列表和可选返回类型。
- 返回控制流检查：带返回值函数的最后顶层语句可以是 `return`，也可以是完整 `if / else if / else` 返回分支；循环体内允许局部 `return`，但仍不把 `while` / `for` 视为保证返回路径。
- 赋值和循环检查：赋值目标必须存在且类型不变；`+=`、`-=` 和 `*=` 目标和值必须是 `int`；`while` 条件必须是 `bool`；`for` 起点、终点和步长必须是 `int`，循环变量是循环体局部 `int`；循环体使用符号表副本；`break` / `continue` 只能在循环体内部使用；循环体内的 `return` 会检查返回类型和块内最终位置。
- 表达式检查：`+`、`-`、`*` 和 `/` 都只接受 `int`；`*` 与 `/` 位于 `+` / `-` 下层，优先级更高；静态除零字面量会报错；括号表达式使用内部表达式类型。

### `lai_backend.py`

通用后端边界模块，只定义不可变 `Backend(name, source_suffix, emit, build)` 描述符；不拥有具体后端、注册表或 CLI 选择。

### `lai_c_backend.py`

C 后端模块，包含：

- `generate_c`：供直接调用者使用，检查后生成完整 C 源码字符串。
- `_generate_checked_c`：对已检查 AST 生成 C 源码。
- `build_c`：通过共享 clang runner 构建 C 输出。
- `C_BACKEND`：默认 C 后端描述符。
- 内部语句/表达式到 C 的转换 helper。

### `lai_clang.py`

共享 clang 调用模块。`build_with_clang` 负责生成物的构建以及既有 clang 缺失/失败错误措辞。

### `lai_llvm_backend.py`

实验性文本 LLVM IR 后端。不使用 `llvmlite`，接受空 `main` 或顶层 `PrintStmt.value` 中的 `IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；变量、赋值、比较、布尔、字符串、控制流和用户函数会产生带行号的 LLVM 能力错误。计算零除数及 `INT_MIN / -1`、`INT_MIN % -1` 仅由 LLVM lowering 拒绝；`build_llvm` 复用 `lai_clang.build_with_clang`。

### `lai_stdlib.py`

内部标准库/运行时 C 输出辅助模块，包含：

- `c_preamble`：生成 C preamble 行，例如 `#include <stdio.h>`。
- `escape_c_string`：把 LAI/Python 字符串内容转成 C 字符串字面量。
- `c_print_string_literal`：生成字符串字面量的 `printf`。
- `c_print_value`：根据 `string`、`int`、`bool` 生成变量或表达式的 `printf`。

### `tests/test_lai_compiler.py`

翻译层测试。它不依赖 `clang`，因此可以快速验证语法、符号表和生成 C 的行为。

### `tests/test_lai_stdlib.py`

内部标准库边界测试。覆盖 C preamble、字符串转义和 `print` 输出格式。

### `tests/test_lai_module_boundaries.py`

模块边界测试。确保 `lai_compiler.py` 对外兼容导出 `LaiCompileError`、`check_program` 和
`generate_c`，同时验证拆出的 checker/backend 可直接处理 parser 生成的 AST。

### `tests/test_lai_ast.py`

AST 边界测试。确保 `lai_ast.py` 是 AST 节点来源，parser 会生成共享 AST 节点，
checker/backend 也直接 import 这些节点。

### `build/`

生成目录：

- `build/main.c`
- `build/main.exe`

这些不是源文件。

### `docs/`

项目文档：

- `docs/Document/`：远期语言愿景和落地路线。
- `docs/superpowers/`：v0 设计与实施计划。
- `docs/ai/`：给未来 AI/agent 接手用的项目记忆。

## 数据流

1. 用户执行 `python lai_compiler.py main.ly --run`。
2. CLI 读取 `main.ly`。
3. `compile_source` 调用 `parse_source`。
4. `tokenize` 生成 token 列表，并忽略 `//` 单行注释。
5. parser 解析多个顶层 `fn`，要求存在无参数、无返回类型的 `main`，解析用户函数参数列表、可选 `-> type` 返回类型、调用实参、调用表达式、加法/减法/乘法/除法/取模表达式、括号表达式、`return`、`while`、`for`、可选 `step`、`through` 包含终点边界、`break`、`continue`、普通赋值、`+=`、`-=`、`*=`、`/=` 和 `%=` 语句，并用 `lai_ast.py` 的节点构造 AST；`*`、`/` 和 `%` 比 `+` / `-` 绑定更紧；`if` 语句可以带可选 `else` 分支，`else if` 会被表示成嵌套 `IfStmt`。
6. `lai_checker.check_program` 读取共享 AST，收集用户函数签名，并为每个函数建立局部符号表；函数参数先进入局部符号表，再检查 `string`、`int`、`bool` 的基础类型规则、加法/减法/乘法/除法/取模操作数类型、括号内部表达式类型、调用表达式类型、赋值类型、`+=` / `-=` / `*=` / `/=` / `%=` 的 `int` 目标和值、`/`、`/=`、`%` 和 `%=` 的显式静态除零、`while` 条件、`for` 起止和步长表达式、循环控制语句位置和返回值规则；返回值函数会递归检查完整 `if / else if / else` 返回路径，也会检查循环体内局部 `return` 的类型和块内位置；then/else/while/for 分支各使用符号表副本。
7. `compile_source` 默认将已检查 AST 交给完整 `C_BACKEND.emit`；`lai_c_backend._generate_checked_c` 生成 C 代码，无返回值函数对应 `static void name(...)`，带返回值函数对应 `static int name(...)` 或 `static const char* name(...)`；减法表达式生成 `left - right`，乘法表达式生成 `left * right`，除法表达式生成 `left / right`，取模表达式生成 `left % right`，括号表达式生成带括号的 C 表达式；`while` 生成 C `while (...) { ... }`，`for ... to ...` 生成 C `for (int i = start; i < end; i = i + step) { ... }`，`for ... through ...` 生成 C `for (int i = start; i <= end; i = i + step) { ... }`，普通赋值生成 `name = value;`，`+=` 生成 `name = name + value;`，`-=` 生成 `name = name - value;`，`*=` 生成 `name = name * value;`，`/=` 生成 `name = name / value;`，`%=` 生成 `name = name % value;`，循环控制生成 `break;` / `continue;`，返回语句生成 `return value;`。
   C preamble、字符串转义和 `printf` 输出行由 `lai_stdlib.py` 提供。
8. `compile_file` 通过选定后端写入 `build/main.c` 或 `examples/build/llvm_minimal.ll`。
9. 后端构建函数均通过 `lai_clang.build_with_clang` 编译为 `.exe`。
10. `--run` 存在时执行生成的 `.exe`。

## 错误模型

编译错误统一抛出 `LaiCompileError`，尽量带行号和直接原因。CLI 捕获后输出：

```text
LAI compile error: ...
```

当前错误主要来自：

- 缺失 `fn main() {`
- 缺失结束 `}`
- 非法变量名
- 重复变量定义
- 未知变量
- 重复函数定义
- 未知函数调用
- 函数参数数量不匹配
- 函数参数类型不匹配
- 重复参数名
- 无效参数类型
- `main` 函数带参数
- `main` 函数带返回类型
- 无效返回类型
- 带返回值函数没有保证所有路径返回
- `return` 类型不匹配
- `return` 后继续写同一块内语句
- 无返回值函数里使用 `return`
- 无返回值函数调用被当作表达式使用
- `while` 条件不是 `bool`
- `for` 起点或终点不是 `int`
- `for` 步长不是 `int` 或显式为 `0`
- `for` 循环变量重复已有变量
- `for` 循环变量在循环外使用
- `while true { return ... }` 作为函数唯一主体时仍缺少最终返回
- 给未知变量赋值
- 赋值类型不匹配
- `break` / `continue` 出现在循环外
- 不支持的语句
- 不支持的 `let` 值
- 不完整的整数加法表达式，例如 `1 +`
- 不完整的整数减法表达式，例如 `1 -`
- 不完整的整数乘法表达式，例如 `1 *`
- 不完整的整数除法表达式，例如 `8 /`
- 不完整的整数取模表达式，例如 `7 %`
- 不完整的比较表达式，例如 `1 <`
- 非布尔 `if` 条件，例如 `if 1 { ... }`
- 非整数加法操作数，例如 `1 + "x"`
- 非整数减法操作数，例如 `1 - "x"`
- 非整数乘法操作数，例如 `1 * "x"`
- 非整数除法操作数，例如 `8 / "x"`
- 非整数取模操作数，例如 `7 % "x"`
- 非整数 `/=` 目标或右侧值，例如 `name /= 2`、`count /= true`
- 非整数 `%=` 目标或右侧值，例如 `name %= 2`、`count %= true`
- 静态除零表达式，例如 `8 / 0`
- 静态 `/=` 除零，例如 `count /= 0` 和 `count /= (0)`
- 静态取模除零，例如 `7 % 0` 和 `7 % (0)`
- 静态 `%=` 取模除零，例如 `count %= 0` 和 `count %= (0)`
- 非整数比较操作数，例如 `"JD" == 3`
- `+=`、`-=`、`*=`、`/=` 或 `%=` 用在非 `int` 目标或非 `int` 值上
- `clang` 不可用或编译失败

## 未来拆分信号

暂时不需要拆模块。出现以下情况时再拆：

- 表达式语法超过当前简单整数加法和基础比较。
- 语句种类超过 5 类。
- 错误恢复或 AST 测试变得困难。
- LLVM 子集暂停在 v0.33 的整数算术表达式 lowering；下一步是 v0.34 负数和一元整数表达式，实施前先向用户提供语法候选。

可能的未来模块：

- `lexer.py`
- `parser.py`
- `ast_nodes.py`
- `checker.py`
- `c_backend.py`
- `cli.py`
