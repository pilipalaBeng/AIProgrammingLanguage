# 架构地图

最后更新：2026-09-07

## 当前架构总览

```text
LAI source (.ly)
    |
    v
compile_source(source)
    |
    +-- tokenize source, skipping // comments
    +-- parse top-level fn blocks into AST
    +-- check symbols, expression types, and control-flow outcomes
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

当前架构仍保持单 CLI 入口。v0.40 第一阶段默认走完整 C 路径，在局部数组创建、读取和边界检查上新增元素修改，并通过 `--backend {c,llvm}` 保留实验性 LLVM 文本 IR 路径。`lai_checker.py` 的内部 `FlowOutcome` 规则继续有效；数组类型信息由 `lai_types.py` 共享。LLVM 仍只支持纯静态顶层整数 `print` 子集，数组、动态值、控制流和用户函数不支持。

## 文件职责

### `main.ly`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `examples/basic_comparisons.ly`

v0.35 的 C 后端可运行示例，覆盖六种比较符和 `int`、`bool`、`string` 相等比较。

### `examples/boolean_logic.ly`

v0.36 的 C 后端布尔逻辑示例，覆盖比较组合、优先级、括号、双重 `not` 和左右短路。

### `examples/runtime_integer_safety.ly`

v0.37 的 C 后端示例：动态参数加法通过 checked helper，`for` 动态 start/end/step 展示 i32 上界的正常完成。

### `examples/general_early_return.ly`

v0.38 的 C 后端示例：覆盖 guard clause、循环路径返回和静态 `while true` 保证返回；真实 C 可执行文件依次输出 `-1`、`0`、`1`、`7`、`8`。同一示例走 LLVM 时按预期报 `line 1: LLVM backend does not support FunctionDef yet`。

### `lai_compiler.py`

v0.40 第一阶段编译器入口，包含：

- `LaiCompileError`：编译错误类型。
- `Token` 与 `tokenize`：词法分析，支持关键字、标识符、字符串、整数、算术/复合赋值、比较、`and`、`or`、`not`、`:`、`,`、`->`、`step`、`through` 和 `//` 注释；双字符 token 采用最长匹配，`&&`、`||`、单独 `!` 不作为源码别名。
- `Program`、`Param`、`FunctionDef`、语句节点，以及 `StringExpr`、`IntExpr`、`UnaryExpr`、算术节点、`GroupExpr`、`BoolExpr`、`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、`NameExpr`、`CallExpr`：从 `lai_ast.py` 兼容导出的 AST 节点。
- `parse_source`：把 LAI 源码解析成 AST。
- 数组前端：词法支持 `[` / `]`；`_parse_type_name` 读取后缀类型，`_parse_array_expr` 读取字面量，后缀索引先于一元运算。parser 接受类型形式后由 checker 拒绝数组签名、多维或通用标量标注，不等于这些能力已开放。
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

### v0.39 数组 AST 与 `lai_types.py`

- `lai_ast.py` 新增不可变 `ArrayExpr(elements, line)` 和 `IndexExpr(target, index, line)`。
- `LetStmt` 末尾新增默认 `None` 的 `type_name`，保留旧位置参数构造。
- `lai_types.py` 定义不可变 `ArrayType(element_type, length)`；长度是局部符号信息，不写入源码类型。
- `ARRAY_TYPES` 只包含 `int[]`、`string[]`、`bool[]`；`array_target_name` 只接受局部数组名及其括号形式。

### `lai_checker.py`

v0.40 第一阶段新增 `IndexAssignStmt(target: IndexExpr, operator, value, line)`，由 `lai_ast.py` 定义、`lai_compiler.py` 兼容导出。`_check_index_assignment` 复用 `_infer_index_type`，三种元素允许同型 `=`，复合赋值只接受 `int`；保留静态零除检查，语句正常 fallthrough，不改变数组类型和长度。

语义和基础类型检查模块，包含：

- `check_program`：检查整个 AST。
- `collect_function_names`：收集并校验用户函数名。
- `collect_function_signatures`：收集并校验用户函数签名，用于调用参数数量、参数类型和返回类型检查。
- `FunctionSignature`：记录参数类型列表和可选返回类型。
- `_check_array_declaration`：只接受显式一维数组声明和直接字面量初始化，逐个检查同构元素后才把数组加入符号表；自身初始化引用不会提前可见。
- `_infer_index_type`：索引目标必须是局部数组、索引必须为 `int`；复用 `evaluate_static_i32` 检查静态范围，结果返回元素标量类型。
- 数组不能作为整体流转：拒绝数组参数/返回、整体复制/赋值/比较/打印；索引结果可复用现有标量表达式、实参和返回规则。
- `FlowOutcome`：checker 内部控制流枚举，不是公共 API 或源码语法；统一表示 fallthrough、return、break、continue 和 divergence。
- 返回控制流检查：支持 guard clause、嵌套/循环路径返回、首条不可达语句诊断和精确所有路径返回；保留缺少返回诊断 `function <name> must end with return`。
- 循环控制流检查：普通 `while` 和所有 `for` 保守包含 fallthrough 并传播嵌套 divergence；静态 true 只识别字面量 `true` 及其 `GroupExpr` 包裹；当前循环的 break/continue 由该循环消费。
- 赋值和循环检查：赋值目标必须存在且类型不变；五种复合赋值目标和值必须是 `int`；`while` 条件必须是 `bool`；`for` 起点、终点和步长必须是 `int`，循环变量是循环体局部 `int`；循环体使用符号表副本；`break` / `continue` 只能在循环体内部使用。
- 表达式检查：算术只接受 `int`；`< <= > >=` 只接受两个 `int`，`== !=` 接受同类型的 `int`、`bool` 或 `string`；`not`、`and`、`or` 只接受 `bool` 并返回 `bool`，无 truthiness。优先级依次为分组/基础表达式、一元、乘除取模、加减、比较、`not`、`and`、`or`；`lai_int.py` 让共享 checker 在进入任一后端前拒绝纯静态零除、每个 i32 中间溢出和静态非正 step。

### `lai_backend.py`

通用后端边界模块，只定义不可变 `Backend(name, source_suffix, emit, build)` 描述符；不拥有具体后端、注册表或 CLI 选择。

### `lai_c_backend.py`

C 后端模块，包含：

- `generate_c`：供直接调用者使用，检查后生成完整 C 源码字符串。
- `_generate_checked_c`：对已检查 AST 生成 C 源码。
- `build_c`：通过共享 clang runner 构建 C 输出。
- `C_BACKEND`：默认 C 后端描述符。
- 内部语句/表达式到 C 的转换 helper；每次生成使用 collision-free 内部前缀，动态 i32 算术和复合赋值调用 checked runtime helper，`for` 固定三个值并通过范围感知推进更新。
- `int` / `bool` 比较直接生成 C 运算符；字符串 `==` / `!=` 生成 `strcmp(...) == 0` / `!= 0`。
- 逻辑非、逻辑与、逻辑或分别生成 `!`、`&&`、`||`，并为每层 AST 保留括号；C 的求值规则提供从左到右短路。
- `CArrayBinding` 关联 `ArrayType` 与内部存储名；`_array_declaration_to_c` 声明局部 C 数组并逐条初始化，保证元素从左到右各求值一次，且不会遮蔽同名用户函数。
- `_index_to_c_value` 对静态合法索引直接生成访问，对动态索引在表达式原位置调用检查 helper；索引只求值一次，逻辑短路不变。
- `_index_assignment_to_c` 先保存已检查的元素地址，再读取旧值（复合赋值），再求值右值，最后经 checked i32 helper（复合赋值）写回；各阶段为独立 C 完整表达式且单次执行，失败不写入。字符串使用 `const char**` slot，仅替换元素指针，不修改字符串字节。
- `int` / `bool` 数组使用 C `int`，字符串数组使用 `const char*`；空数组物理占位 1、逻辑长度 0，任何索引都越界。不用零长 C 数组、VLA、堆分配或 GC，存储随局部块生命周期结束。

### `lai_clang.py`

共享 clang 调用模块。`build_with_clang` 负责生成物的构建以及既有 clang 缺失/失败错误措辞。

### `lai_llvm_backend.py`

实验性文本 LLVM IR 后端。不使用 `llvmlite`，接受空 `main` 或顶层 `PrintStmt.value` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；一元 `+` 透传，一元 `-` 生成 `sub i32 0, value` 或 `INT_MIN` 常量。共享 checker 在 lowering 前拒绝纯静态零除和每个 i32 中间溢出，因此 LLVM 不再接受源码层静态回绕。含动态表达式、变量、赋值、比较、布尔、字符串、控制流或用户函数的有效 LAI 会产生带行号的能力错误；`LogicalNotExpr` 与 `LogicalExpr` 仍明确不支持。`build_llvm` 复用 `lai_clang.build_with_clang`。

### `lai_stdlib.py`

内部标准库/运行时 C 输出辅助模块，包含：

- `c_preamble`：生成 `#include <stdio.h>`、`#include <string.h>`、`#include <limits.h>`、`#include <stdint.h>` 和 `#include <stdlib.h>`。
- `c_runtime_support`：按本次生成选择的内部前缀输出 checked i32、运行时错误、动态正 step 和范围推进 helper。
- `c_array_runtime_support`：仅程序包含数组时输出动态索引 helper，访问前检查上下界，失败输出行号、index、length 并 `exit(EXIT_FAILURE)`。
- `escape_c_string`：把 LAI/Python 字符串内容转成 C 字符串字面量。
- `c_print_string_literal`：生成字符串字面量的 `printf`。
- `c_print_value`：根据 `string`、`int`、`bool` 生成变量或表达式的 `printf`。

### `examples/local_arrays.ly` 与数组测试

v0.39 示例的 C 实际输出是 `95`、`LAI`、`1`；`bool` 沿用 `%d` 数字打印。完整示例含用户函数，LLVM 实际按预期 exit 1 并报 `LAI compile error: line 1: LLVM backend does not support FunctionDef yet`；纯 main 数组单测则明确验证 `LetStmt` 能力错误。

`tests/test_lai_array_parser.py` 覆盖 AST/解析，`tests/test_lai_arrays.py` 覆盖类型、静态边界、作用域和标量复用，`tests/test_lai_array_runtime.py` 使用真实 `clang` 验证动态边界、初始化顺序、索引单次求值、短路和内部命名。

v0.40 第一阶段新增 `tests/test_lai_array_assignment.py` 与 `tests/test_lai_array_assignment_runtime.py`。`examples/array_element_assignment.ly` 默认 C 和严格 C11 / `-O2` 均输出 `85`、`60`、`10`、`after`、`1`；LLVM 按预期以第 1 行 `FunctionDef` 能力错误退出。最终完整回归 480 项通过、无 skip，详细验证见 `active-context.md` 的 2026-09-07 记录。

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
7. `compile_source` 默认将已检查 AST 交给完整 `C_BACKEND.emit`；`lai_c_backend._generate_checked_c` 生成既有 C 结构，动态整数表达式调用 checked helper，逻辑 AST 递归发射带括号的 `!` / `&&` / `||`，不提前求值右侧，从而保持从左到右短路。
   C preamble、checked runtime、字符串转义和 `printf` 输出行由 `lai_stdlib.py` 提供。
8. `compile_file` 通过选定后端写入 `build/main.c` 或 `examples/build/llvm_minimal.ll`。
9. 后端构建函数均通过 `lai_clang.build_with_clang` 编译为 `.exe`。
10. `--run` 存在时执行生成的 `.exe`。

数组经过同一管线：parser 构造带类型的 `LetStmt` / `ArrayExpr` / `IndexExpr`，checker 写入 `ArrayType` 并检查同构元素和静态范围，C 后端顺序初始化内部数组存储，动态索引由 runtime helper 在访问前检查。该路径不提供数组逃逸、复制或整体赋值。

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
- 数组声明缺少显式类型、元素类型不一致、索引不是 `int` 或目标不是局部数组
- 编译期可算出的数组越界：`line N: array index out of bounds: index I, length L`
- 数组参数/返回、整数组复制/赋值/比较/打印等未支持操作
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

动态数组越界属于运行时错误：向 `stderr` 输出 `LAI runtime error: line N: array index out of bounds: index I, length L` 并以 `EXIT_FAILURE` 退出，不继续访问内存。

## 未来拆分信号

暂时不需要继续拆模块。出现以下情况时再拆：

- v0.36 之后继续增加表达式层，可能让 parser 入口难以局部理解或测试。
- lexer 与 parser 需要独立错误恢复、源码跨度或诊断上下文。
- 错误恢复或 AST 测试变得困难。
- C 与 LLVM 前端共享逻辑开始在入口模块中重复。

LLVM 子集仍不支持数组、`CompareExpr`、`LogicalNotExpr` 和 `LogicalExpr`；动态值、变量、控制流和用户函数仍不支持。当前 v0.40 第一阶段已实现元素修改，长度 API 和遍历仍在 v0.40 待实现；多维数组仍在 v0.41。v0.40-v0.45 共 6 个编号版本尚有工作，后续为反向循环、字符串/最小用户标准库、浮点数、LLVM 变量模型与语义复盘。数组参数/返回和整数组复制/赋值属于未编号候选，须先明确生命周期和复制语义。

可能的未来模块：

- `lexer.py`
- `parser.py`
- `ast_nodes.py`
- `checker.py`
- `c_backend.py`
- `cli.py`
