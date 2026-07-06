# 架构地图

最后更新：2026-07-06

## 当前架构总览

```text
LAI source (.lai)
    |
    v
compile_source(source)
    |
    +-- validate entry: fn main() { ... }
    +-- parse line-oriented statements
    +-- maintain symbol table
    +-- emit C lines
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

### `main.lai`

最小 LAI 示例程序。用于端到端编译和运行验证。

### `lai_compiler.py`

v0 编译器主体，包含：

- `LaiCompileError`：编译错误类型。
- `compile_source`：把 LAI 源码字符串翻译成 C 源码字符串。
- `compile_file`：读取 `.lai` 文件，写出 C 文件，调用 `clang`。
- `_compile_statement`：处理单行 `let` 和 `print`。
- `_compile_value`：处理字符串和整数值。
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

1. 用户执行 `python lai_compiler.py main.lai --run`。
2. CLI 读取 `main.lai`。
3. `compile_source` 校验入口和结束块。
4. 编译器逐行处理 `let` 与 `print`。
5. 编译器用 `symbols` 记录变量名和类型：`string` 或 `int`。
6. 编译器生成 C 代码。
7. `compile_file` 写入 `build/main.c`。
8. `_run_clang` 编译为 `build/main.exe`。
9. `--run` 存在时执行生成的 `.exe`。

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
- 不支持的语句
- 不支持的 `let` 值
- `clang` 不可用或编译失败

## 未来拆分信号

暂时不需要拆模块。出现以下情况时再拆：

- 表达式语法超过字面量和变量名。
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
