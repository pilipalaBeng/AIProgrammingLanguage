# 架构地图

最后更新：2026-07-07

## 当前架构总览

```text
LAI source (.ly)
    |
    v
compile_source(source)
    |
    +-- tokenize source, skipping // comments
    +-- parse top-level fn blocks into AST
    +-- validate symbols during C codegen
    +-- emit readable C lines
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

当前架构故意保持单文件、单后端、单入口，方便快速验证语言雏形。

## 文件职责

### `main.ly`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `lai_compiler.py`

v0.5 编译器主体，包含：

- `LaiCompileError`：编译错误类型。
- `Token` 与 `tokenize`：词法分析，支持关键字、标识符、字符串、整数、`+`、`<`、`>`、`==` 和 `//` 注释。
- `Program`、`FunctionDef`、`LetStmt`、`PrintStmt`、`IfStmt`、`CallStmt`、`StringExpr`、`IntExpr`、`AddExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`：AST 节点。
- `parse_source`：把 LAI 源码解析成 AST。
- `generate_c`：把 AST 生成 C 源码字符串。
- `compile_source`：把 LAI 源码字符串翻译成 C 源码字符串。
- `compile_file`：读取 `.ly` 文件，写出 C 文件，调用 `clang`。
- `_run_clang`：调用本机 `clang`。
- `main`：命令行入口。

### `tests/test_lai_compiler.py`

翻译层测试。它不依赖 `clang`，因此可以快速验证语法、符号表和生成 C 的行为。

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
5. parser 解析多个顶层 `fn`，要求存在 `main`，并解析 `let`、`print`、`if`、函数调用、简单整数加法、布尔值和比较表达式。
6. `generate_c` 先收集用户函数名并生成 C 原型，再用 `symbols` 记录每个函数内部的变量名和类型：`string`、`int` 或 `bool`。
7. 编译器生成 C 代码，用户函数对应 `static void name(void)`。
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
- 非布尔 `if` 条件
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
