# 当前上下文

最后更新：2026-07-06

## 当前工作状态

仓库已经具备 LAI v0.1 的最小可运行编译器：

- `main.lai` 是示例输入。
- `lai_compiler.py` 负责解析、校验、生成 C、调用 `clang`。
- `tests/test_lai_compiler.py` 覆盖核心翻译行为和错误行为。
- `build/main.c` 与 `build/main.exe` 是生成物。

本轮新增了 `print(123)` 这种整数字面量打印能力。`print(...)` 现在支持字符串字面量、
整数字面量和已定义变量。

本轮文档工作补齐了原本为空的 `AGENTS.md` 和 `docs/ai` 项目记忆文件，方便后续 agent
快速接手。

## 最近的重要事实

- 工作目录不是 git 仓库；`git status` 当前不可用。
- `docs/ai` 下的项目记忆文件原本都是空文件。
- 原有决策文件名 `0001-auth-design.md` 像模板残留，和当前编译器项目不匹配。
- 当前 v0 仍使用英文关键字和 `{}` 块语法；远期中文名“灵语”不等于当前要使用中文关键字。

## 下一步优先级

建议按这个顺序推进：

1. 继续加语言最小能力：注释、简单表达式、布尔值、`if` 或基础函数调用只能择一推进。
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
python lai_compiler.py main.lai --run
```

## 2026-07-06 v0.1 Compiler Architecture Update

The compiler has been refactored internally into a structured pipeline:

```text
source -> lexer -> parser -> AST -> C codegen -> clang
```

The public CLI and v0 language behavior remain stable. Future syntax work
should extend the lexer, parser, AST nodes, and C code generator in that order,
with tests added before implementation.
