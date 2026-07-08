# LAI 版本路线图

最后更新：2026-07-08

## 目的

本文记录 LAI 当前原型阶段的版本规划，帮助后续开发保持小步推进。这里的版本号代表项目阶段目标，不代表已经发布的稳定语言规范。

每个版本都应保持：

- 范围小，可测试，可运行。
- 新语法先写测试，再改编译器。
- 优先保持 `lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang` 管线稳定。
- 不把远期愿景文档里的能力提前描述为已实现。

## 当前版本

### v0.11：`else if` 链式分支

状态：已完成。

目标：

- 支持 `else if condition { ... }`。
- 支持多段 `else if` 链。
- 支持链尾继续写普通 `else`。
- 不新增单词关键字 `elseif`。
- parser 将 `else if` 表示成 else 分支里的嵌套 `IfStmt`。

意义：

- 让多分支条件判断更好写。
- 复用 v0.10 的 `IfStmt.else_statements`，不扩大 AST 类型数量。
- 避免把这个小语法糖拖到后期和循环、返回值、LLVM 后端混在一起。

当前支持：

- `if ready { ... }`
- `if false { ... } else { ... }`
- `if false { ... } else if true { ... } else { ... }`
- 多段 `else if` 链。

## 已完成

### v0.10：最小 `else`

状态：已完成。

目标：

- 支持 `if condition { ... } else { ... }`。
- 支持 `else` 写在右花括号同一行或下一行。
- `else` 分支参与语义/类型检查。
- then/else 分支使用独立符号表副本，分支内变量不互相泄漏。
- C 后端生成 `if (...) { ... } else { ... }`。

意义：

- 补齐最小条件分支闭环。
- 验证 v0.9 共享 AST 边界能顺利承载新语法。
- 在不引入循环和完整作用域系统的前提下，继续小步扩展控制流。

当前支持：

- `if ready { ... }`
- `if 1 < 2 { ... }`
- `if false { ... } else { ... }`
- `IfStmt.else_statements`

### v0.9：AST 节点拆分

状态：已完成。

目标：

- 新增 `lai_ast.py`，集中定义 `Program`、语句节点和表达式节点。
- `lai_compiler.py` 的 parser 使用 `lai_ast.py` 中的节点创建 AST。
- `lai_checker.py` 和 `lai_c_backend.py` 直接 import AST 节点，使用 `isinstance(...)` 判断节点类型。
- `lai_compiler.py` 继续兼容导出 AST 节点，保持旧测试和脚本可用。

意义：

- 让 AST 成为 parser、checker、backend 的共享边界。
- 消除 checker/backend 通过类名字符串判断 AST 节点的做法。
- 为后续继续拆 lexer/parser 或新增 `else` 打基础。

当前支持：

- 正式源码扩展名：`.ly`
- 示例命令：`python lai_compiler.py main.ly --run`
- `lai_ast.Program`
- `lai_ast.LetStmt`、`PrintStmt`、`IfStmt`、`CallStmt`
- `lai_ast.StringExpr`、`IntExpr`、`AddExpr`、`BoolExpr`、`CompareExpr`、`NameExpr`

### v0.8：编译器模块拆分

状态：已完成。

目标：

- 新增 `lai_core.py`，集中共享错误类型和核心名称规则。
- 新增 `lai_checker.py`，承载 `check_program(program)` 和语义/类型检查。
- 新增 `lai_c_backend.py`，承载 `generate_c(program)` 和 C 后端输出。
- `lai_compiler.py` 保留 lexer、parser、CLI 和兼容导出入口。

意义：

- 降低单文件编译器继续膨胀的风险。
- 让后续新增语法时能分别改 checker 和 backend。
- 保持旧导入路径可用，避免破坏现有测试和用户脚本。

当前支持：

- `lai_core.LaiCompileError`
- `lai_checker.check_program(program)`
- `lai_c_backend.generate_c(program)`

### v0.7：小型标准库雏形

状态：已完成。

目标：

- 新增 `lai_stdlib.py`，作为标准库/运行时 C 输出辅助模块。
- 集中管理 C preamble，例如 `#include <stdio.h>`。
- 集中管理 LAI 字符串到 C 字符串字面量的转义规则。
- 集中管理 `print` 对 `string`、`int`、`bool` 的 C `printf` 输出格式。

意义：

- 给后续真正的标准库和运行时能力留出清楚边界。
- 让 C codegen 少负责底层输出细节。
- 避免未来新增运行时辅助函数时继续堆进 `lai_compiler.py`。

当前支持：

- 内部标准库模块：`lai_stdlib.py`
- `c_preamble()`、`escape_c_string()`、`c_print_string_literal()`、`c_print_value()`

### v0.6：基础类型检查和错误提示

状态：已完成。

目标：

- 引入独立的 `check_program(program)` 语义/类型检查阶段。
- 明确当前表达式类型：`string`、`int`、`bool`。
- 在生成 C 之前检查变量、函数调用、`if` 条件、整数加法和比较表达式。
- 让类型错误信息包含实际类型，例如 `got string and int` 或 `got int`。

意义：

- 把语义检查从 C 生成阶段前置出来，后续更容易扩展。
- 降低后续加入 `else`、函数参数、返回值等能力时的不确定性。
- 让错误行为更适合测试和文档化。

当前支持：

- `check_program(program)` 可单独检查 AST。
- `if` 条件必须是 `bool`。
- 比较表达式当前要求两侧都是 `int`。
- 整数加法当前要求所有参与项都是 `int`。

### v0.5：正式源码扩展名 `.ly`

状态：已完成。

目标：

- 将正式源码扩展名从 `.lai` 切换为 `.ly`。
- 将示例文件从 `main.lai` 重命名为 `main.ly`。
- CLI 帮助文本展示 `.ly source file`。
- 旧 `.lai` 文件暂时仍可作为普通输入文件编译，不在编译器层强制禁止。

意义：

- 让源码文件名更短，更贴合“灵语 / LingYu”的身份。
- 避免 `.ai` 等高冲突扩展名。
- 在语言早期就固定更顺手的文件入口。

### v0.4：用户自定义函数

状态：已完成。

目标：

- 支持定义零参数、无返回值的用户函数，例如 `fn greet() { ... }`。
- 支持从 `main` 或其他用户函数中调用用户函数，例如 `greet()`。
- 生成 C 的 `static void` 函数和函数原型声明。
- 暂不支持函数参数、返回值、重载、闭包或模块系统。

当前支持：

- `fn main() { ... }`
- `fn greet() { ... }`
- `// comment`
- `let name = "text"`
- `let count = 123`
- `let count = 1 + 2`
- `let ready = true`
- `let ok = count == 3`
- `print("text")`
- `print(123)`
- `print(1 + 2)`
- `print(true)`
- `print(1 < 2)`
- `print(name)`
- `if ready { ... }`
- `if 1 < 2 { ... }`
- `greet()`

### v0.3：布尔值、比较表达式和 `if`

状态：已完成。

目标：

- 支持布尔值：`true`、`false`。
- 支持基础比较表达式：`1 < 2`、`count == 3`、`3 > 2`。
- 支持最小 `if` 语句。
- 暂不支持 `else`、循环、括号表达式或完整运算符优先级。

### v0.2：注释和简单表达式

状态：已完成。

目标：

- 支持 `// comment` 单行注释。
- 支持简单整数加法表达式，例如 `print(1 + 2)`。
- 支持 `let count = 1 + 2`。
- 保持表达式范围极小，暂不加入优先级复杂的多运算符体系。

### v0.1：结构化编译器管线

状态：已完成。

目标：

- 建立 `source -> lexer -> parser -> AST -> C codegen -> clang` 管线。
- 保持 `python lai_compiler.py main.ly --run` 可用。
- 支持最小语法闭环。

## 近期规划

### v0.12：函数参数或返回值

建议目标：

- 开始函数参数和返回值的最小设计，先择一推进。
- 保持函数调用、类型检查和 C 后端行为可测试。
- 保持 C 后端稳定。

意义：

- 避免单文件编译器过大。
- 为后续更多语言能力提供更清楚的模块边界。

## 远期探索

### 数据结构命名与设计

建议目标：

- 未来数组类型优先采用 C# 风格写法，例如 `int[]`。
- 未来键值表类型优先命名为 `dict`，避免和集合操作 `.map(...)` 混淆。
- 具体语法和实现顺序见 `docs/ai/data-structures-roadmap.md`。

意义：

- 提前锁定数组和字典的命名方向。
- 让后续设计集合、张量和结构化数据时有一致起点。
- 明确这些能力尚未实现，避免混入当前 v0.x 行为说明。

### v0.13+：LLVM 后端探索

建议目标：

- 在 C 后端稳定后，再探索 LLVM IR。
- 不要同时大改语法和后端。
- 先选一个极小程序验证 LLVM 生成链路。

意义：

- 为长期高性能方向做准备。
- 保持每一步都有可运行闭环。

## 暂不规划进近期版本的能力

- GC。
- JIT。
- 并发调度。
- 包管理。
- 模块系统。
- 泛型。
- 宏系统。
- AI 自动优化能力。

这些属于远期方向，当前不应压进 v0.x 早期闭环。
