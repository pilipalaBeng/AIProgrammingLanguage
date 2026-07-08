# 架构地图

最后更新：2026-07-08

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
    +-- emit readable C lines with stdlib helpers
    |
    v
generated C
    |
    v
clang
    |
    v
native .exe
```

当前架构仍保持单后端和单 CLI 入口，但 v0.11 已拆出 AST、核心错误、checker 和 C backend，
方便后续新增语言能力时分别修改语法节点、语义检查和代码生成。

## 文件职责

### `main.ly`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `lai_compiler.py`

v0.11 编译器入口，包含：

- `LaiCompileError`：编译错误类型。
- `Token` 与 `tokenize`：词法分析，支持关键字、标识符、字符串、整数、`+`、`<`、`>`、`==` 和 `//` 注释。
- `Program`、`FunctionDef`、`LetStmt`、`PrintStmt`、`IfStmt`、`CallStmt`、`StringExpr`、`IntExpr`、`AddExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`：从 `lai_ast.py` 兼容导出的 AST 节点。
- `parse_source`：把 LAI 源码解析成 AST。
- `check_program`：从 `lai_checker.py` 兼容导出的语义和基础类型检查入口。
- `generate_c`：从 `lai_c_backend.py` 兼容导出的 C 后端入口。
- `compile_source`：把 LAI 源码字符串翻译成 C 源码字符串。
- `compile_file`：读取 `.ly` 文件，写出 C 文件，调用 `clang`。
- `_run_clang`：调用本机 `clang`。
- `main`：命令行入口。

### `lai_ast.py`

AST 节点模块，包含：

- `Program`：程序根节点。
- `FunctionDef`：用户函数定义。
- `LetStmt`、`PrintStmt`、`IfStmt`、`CallStmt`：语句节点，其中 `IfStmt.else_statements` 保存可选 else 分支；`else if` 表示为 else 分支里的嵌套 `IfStmt`。
- `StringExpr`、`IntExpr`、`AddExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`：表达式节点。

### `lai_core.py`

核心共享模块，包含：

- `LaiCompileError`：编译错误类型。
- `NAME_RE`：函数名和变量名的基础规则。

### `lai_checker.py`

语义和基础类型检查模块，包含：

- `check_program`：检查整个 AST。
- `collect_function_names`：收集并校验用户函数名。

### `lai_c_backend.py`

C 后端模块，包含：

- `generate_c`：生成完整 C 源码字符串。
- 内部语句/表达式到 C 的转换 helper。

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
5. parser 解析多个顶层 `fn`，要求存在 `main`，并用 `lai_ast.py` 的节点构造 AST；`if` 语句可以带可选 `else` 分支，`else if` 会被表示成嵌套 `IfStmt`。
6. `lai_checker.check_program` 读取共享 AST，收集用户函数名，并为每个函数建立局部符号表，检查 `string`、`int`、`bool` 的基础类型规则；then/else 分支各使用符号表副本。
7. `lai_c_backend.generate_c` 在检查通过后生成 C 代码，用户函数对应 `static void name(void)`。
   C preamble、字符串转义和 `printf` 输出行由 `lai_stdlib.py` 提供。
8. `compile_file` 写入 `build/main.c`。
9. `_run_clang` 编译为 `build/main.exe`。
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
- 不支持的语句
- 不支持的 `let` 值
- 不完整的整数加法表达式，例如 `1 +`
- 不完整的比较表达式，例如 `1 <`
- 非布尔 `if` 条件，例如 `if 1 { ... }`
- 非整数加法操作数，例如 `1 + "x"`
- 非整数比较操作数，例如 `"JD" == 3`
- `clang` 不可用或编译失败

## 未来拆分信号

暂时不需要拆模块。出现以下情况时再拆：

- 表达式语法超过当前简单整数加法和基础比较。
- 语句种类超过 5 类。
- 错误恢复或 AST 测试变得困难。
- C 后端之外需要第二个后端。

可能的未来模块：

- `lexer.py`
- `parser.py`
- `ast_nodes.py`
- `checker.py`
- `c_backend.py`
- `cli.py`
