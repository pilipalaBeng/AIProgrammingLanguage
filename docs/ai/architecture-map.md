# 架构地图

最后更新：2026-07-28

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

当前架构仍保持单 CLI 入口。v0.36 默认走完整 C 路径，并通过 `--backend {c,llvm}` 提供实验性 LLVM 文本 IR 路径；后端特定的发射和构建不耦合在编译器入口。表达式优先级为分组/基础表达式、一元、乘除取模、加减、比较、`not`、`and`、`or`。`and` / `or` / `not` 是保留关键字，不提供符号源码别名；checker 只接受 `bool` operand，不引入 truthiness。C 后端为每层逻辑 AST 保留括号并生成 `!`、`&&`、`||`，由 C 保证 `and` / `or` 从左到右短路。LLVM 后端不使用 `llvmlite`，仍只支持空 `main` 或顶层整数 `print` 子集；`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、变量、赋值、布尔、字符串、控制流和用户函数会报明确能力错误。`examples/basic_comparisons.ly` 与 `examples/boolean_logic.ly` 是 C 示例，原有三个 LLVM/一元示例保持原能力边界。

## 文件职责

### `main.ly`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `examples/basic_comparisons.ly`

v0.35 的 C 后端可运行示例，覆盖六种比较符和 `int`、`bool`、`string` 相等比较。

### `examples/boolean_logic.ly`

v0.36 的 C 后端布尔逻辑示例，覆盖比较组合、优先级、括号、双重 `not` 和左右短路。

### `lai_compiler.py`

v0.36 编译器入口，包含：

- `LaiCompileError`：编译错误类型。
- `Token` 与 `tokenize`：词法分析，支持关键字、标识符、字符串、整数、算术/复合赋值、比较、`and`、`or`、`not`、`:`、`,`、`->`、`step`、`through` 和 `//` 注释；双字符 token 采用最长匹配，`&&`、`||`、单独 `!` 不作为源码别名。
- `Program`、`Param`、`FunctionDef`、语句节点，以及 `StringExpr`、`IntExpr`、`UnaryExpr`、算术节点、`GroupExpr`、`BoolExpr`、`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、`NameExpr`、`CallExpr`：从 `lai_ast.py` 兼容导出的 AST 节点。
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
- `StringExpr`、`IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`、`BoolExpr`、`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、`NameExpr`、`CallExpr`：表达式节点；`LogicalNotExpr` 表示逻辑非，`LogicalExpr` 表示左结合的逻辑与/或，`GroupExpr` 保留显式括号分组。

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
- 表达式检查：算术只接受 `int`；`< <= > >=` 只接受两个 `int`，`== !=` 接受同类型的 `int`、`bool` 或 `string`；`not`、`and`、`or` 只接受 `bool` 并返回 `bool`，无 truthiness。优先级依次为分组/基础表达式、一元、乘除取模、加减、比较、`not`、`and`、`or`；`lai_int.py` 让 checker 和 C 后端共同拒绝静态可求值为零的除数、一元 `INT_MIN` 溢出和静态非正 step。

### `lai_backend.py`

通用后端边界模块，只定义不可变 `Backend(name, source_suffix, emit, build)` 描述符；不拥有具体后端、注册表或 CLI 选择。

### `lai_c_backend.py`

C 后端模块，包含：

- `generate_c`：供直接调用者使用，检查后生成完整 C 源码字符串。
- `_generate_checked_c`：对已检查 AST 生成 C 源码。
- `build_c`：通过共享 clang runner 构建 C 输出。
- `C_BACKEND`：默认 C 后端描述符。
- 内部语句/表达式到 C 的转换 helper。
- `int` / `bool` 比较直接生成 C 运算符；字符串 `==` / `!=` 生成 `strcmp(...) == 0` / `!= 0`。
- 逻辑非、逻辑与、逻辑或分别生成 `!`、`&&`、`||`，并为每层 AST 保留括号；C 的求值规则提供从左到右短路。

### `lai_clang.py`

共享 clang 调用模块。`build_with_clang` 负责生成物的构建以及既有 clang 缺失/失败错误措辞。

### `lai_llvm_backend.py`

实验性文本 LLVM IR 后端。不使用 `llvmlite`，接受空 `main` 或顶层 `PrintStmt.value` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；一元 `+` 透传，一元 `-` 生成 `sub i32 0, value` 或 `INT_MIN` 常量。变量、赋值、比较、布尔、字符串、控制流和用户函数会产生带行号的 LLVM 能力错误；v0.36 的 `LogicalNotExpr` 与 `LogicalExpr` 仍明确不支持。checker 与 C 后端拒绝静态可求值为零的除数；LLVM lowering 还拒绝 i32 回绕后计算为零的除数及 `INT_MIN / -1`、`INT_MIN % -1`；`build_llvm` 复用 `lai_clang.build_with_clang`。

### `lai_stdlib.py`

内部标准库/运行时 C 输出辅助模块，包含：

- `c_preamble`：生成 `#include <stdio.h>` 和 `#include <string.h>`。
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
5. parser 解析多个顶层 `fn` 和现有语句/表达式；逻辑层在比较层外按 `not`、`and`、`or` 依次展开，构造 `LogicalNotExpr` / `LogicalExpr`。因此比较高于 `not`，`not` 高于 `and`，`and` 高于 `or`；显式 `GroupExpr` 可覆盖该顺序。
6. `lai_checker.check_program` 读取共享 AST，收集用户函数签名并检查既有语义规则；逻辑 operator 只接受 `and` / `or`，所有逻辑 operand 严格为 `bool`，即使右侧运行时会短路也仍做静态检查。
7. `compile_source` 默认将已检查 AST 交给完整 `C_BACKEND.emit`；`lai_c_backend._generate_checked_c` 生成既有 C 结构，逻辑 AST 递归发射带括号的 `!` / `&&` / `||`，不提前求值右侧，从而保持从左到右短路。
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
- 未分组比较链，例如 `1 < 2 < 3`
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
- 大小比较使用非整数操作数，例如 `"A" < "B"`
- 相等比较两侧类型不同，例如 `"JD" == 3`
- `+=`、`-=`、`*=`、`/=` 或 `%=` 用在非 `int` 目标或非 `int` 值上
- `clang` 不可用或编译失败

## 未来拆分信号

暂时不需要继续拆模块。出现以下情况时再拆：

- v0.36 之后继续增加表达式层，可能让 parser 入口难以局部理解或测试。
- lexer 与 parser 需要独立错误恢复、源码跨度或诊断上下文。
- 错误恢复或 AST 测试变得困难。
- C 与 LLVM 前端共享逻辑开始在入口模块中重复。

LLVM 子集仍不支持 `CompareExpr`、`LogicalNotExpr` 和 `LogicalExpr`；动态整数溢出、动态非正 step 和 LLVM 变量/控制流等范围也未实现。当前版本是 v0.36，下一版 v0.37 聚焦运行时整数语义与安全；剩余编号队列为 v0.37-v0.44，共 8 个版本。

可能的未来模块：

- `lexer.py`
- `parser.py`
- `ast_nodes.py`
- `checker.py`
- `c_backend.py`
- `cli.py`
