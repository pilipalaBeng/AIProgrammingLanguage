# AGENTS.md

## 项目定位

这个仓库是 LAI（灵语）v0 编译器原型。当前目标很小：把一个极简 `.ly`
程序经过基础语义/类型检查后默认翻译成 C，再通过 `clang` 编译成 Windows 可执行文件；v0.34 另有受限的实验性文本 LLVM IR 路径。

当前主流程：

```text
main.ly -> lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang -> build/main.exe
```

v0 不是完整语言实现。长期设想可以参考 `docs/Document` 下的中文方案文档，
但当前代码只承诺支持一个最小可运行闭环。

## 默认沟通

- 默认使用简体中文回复。
- 代码、命令、变量名、错误信息、日志和文件路径保持原文。
- 说明代码时优先引用实际文件路径和函数名，不凭空扩展未实现能力。

## 接手前先读

优先阅读这些文件来恢复上下文：

1. `docs/ai/active-context.md`
2. `docs/ai/project-brief.md`
3. `docs/ai/architecture-map.md`
4. `docs/ai/conventions.md`
5. `docs/superpowers/specs/2026-07-23-lai-v0.34-unary-integer-expressions-design.md`
6. `docs/superpowers/plans/2026-07-23-lai-v0.34-unary-integer-expressions.md`
7. `docs/superpowers/specs/2026-07-23-lai-v0.33-llvm-integer-arithmetic-design.md`
8. `docs/superpowers/plans/2026-07-23-lai-v0.33-llvm-integer-arithmetic.md`
9. `docs/superpowers/specs/2026-07-11-lai-v0.32-textual-llvm-backend-design.md`
10. `docs/superpowers/plans/2026-07-13-lai-v0.32-textual-llvm-backend.md`
11. `docs/superpowers/specs/2026-07-11-lai-v0.31-backend-boundary-design.md`
12. `docs/superpowers/plans/2026-07-11-lai-v0.31-backend-boundary.md`
13. `docs/superpowers/specs/2026-07-11-lai-v0.30-modulo-assign-design.md`
14. `docs/superpowers/plans/2026-07-11-lai-v0.30-modulo-assign.md`
15. `docs/superpowers/specs/2026-07-10-lai-v0.29-modulo-expressions-design.md`
16. `docs/superpowers/plans/2026-07-10-lai-v0.29-modulo-expressions.md`
17. `docs/superpowers/specs/2026-07-10-lai-v0.28-divide-assign-design.md`
18. `docs/superpowers/plans/2026-07-10-lai-v0.28-divide-assign.md`
19. `docs/superpowers/specs/2026-07-10-lai-v0.27-division-expressions-design.md`
20. `docs/superpowers/plans/2026-07-10-lai-v0.27-division-expressions.md`
21. `docs/superpowers/specs/2026-07-10-lai-v0.26-multiply-assign-design.md`
22. `docs/superpowers/plans/2026-07-10-lai-v0.26-multiply-assign.md`
23. `docs/superpowers/specs/2026-07-10-lai-v0.25-multiplication-expressions-design.md`
24. `docs/superpowers/plans/2026-07-10-lai-v0.25-multiplication-expressions.md`
25. `docs/superpowers/specs/2026-07-10-lai-v0.24-minus-assign-design.md`
26. `docs/superpowers/plans/2026-07-10-lai-v0.24-minus-assign.md`
27. `docs/superpowers/specs/2026-07-10-lai-v0.23-subtraction-expressions-design.md`
28. `docs/superpowers/plans/2026-07-10-lai-v0.23-subtraction-expressions.md`
29. `docs/superpowers/specs/2026-07-10-lai-v0.22-parenthesized-expressions-design.md`
30. `docs/superpowers/plans/2026-07-10-lai-v0.22-parenthesized-expressions.md`
31. `docs/superpowers/specs/2026-07-10-lai-v0.21-through-loop-design.md`
32. `docs/superpowers/plans/2026-07-10-lai-v0.21-through-loop.md`
33. `docs/superpowers/specs/2026-07-10-lai-v0.20-for-step-design.md`
34. `docs/superpowers/plans/2026-07-10-lai-v0.20-for-step.md`
35. `docs/superpowers/specs/2026-07-09-lai-v0.19-plus-assign-design.md`
36. `docs/superpowers/plans/2026-07-09-lai-v0.19-plus-assign.md`
37. `docs/superpowers/specs/2026-07-09-lai-v0.18-for-loop-design.md`
38. `docs/superpowers/plans/2026-07-09-lai-v0.18-for-loop.md`
39. `docs/superpowers/specs/2026-07-09-lai-v0.17-loop-return-flow-design.md`
40. `docs/superpowers/plans/2026-07-09-lai-v0.17-loop-return-flow.md`
41. `docs/superpowers/specs/2026-07-09-lai-v0.16-break-continue-design.md`
42. `docs/superpowers/plans/2026-07-09-lai-v0.16-break-continue.md`
43. `docs/superpowers/specs/2026-07-09-lai-v0.15-while-assignment-design.md`
44. `docs/superpowers/plans/2026-07-09-lai-v0.15-while-assignment.md`
45. `docs/superpowers/specs/2026-07-09-lai-v0.14-branch-return-flow-design.md`
46. `docs/superpowers/plans/2026-07-09-lai-v0.14-branch-return-flow.md`
47. `docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
48. `docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`

如果要了解远期愿景，再读：

- `docs/Document/AI时代极简高性能编程语言设计方案（含专属命名+AI原生优化特性）.md`
- `docs/Document/零基础非从业人员开发灵语（LAI）编程语言：完整工具+系统+落地步骤.md`

## 当前实现边界

`lai_compiler.py` 当前支持：

- `fn main() { ... }`
- `fn greet() { ... }`
- `fn show(name: string, count: int, ready: bool) { ... }`
- `fn add(a: int, b: int) -> int { ... }`
- 返回值函数可用完整 `if / else if / else` 分支返回
- `greet()`
- `show("JD", 3, true)`
- `// comment`
- `let name = "text"`
- `let count = 123`
- `let count = 1 + 2`
- `let count = (1 + 2)`
- `let count = 5 - 2`
- `let count = 2 * 3`
- `let count = 2 + 3 * 4`
- `let count = (2 + 3) * 4`
- `let count = 8 / 2`
- `let count = (6 + 4) / 2`
- `let count = 7 % 3`
- `let count = (10 + 5) % 4`
- `let count = add(1, 2)`
- `count = count + 1`
- `count += 1`
- `count -= 1`
- `count *= 2`
- `count *= add(1, 2)`
- `count /= 2`
- `count /= (6 / 2)`
- `count %= 3`
- `count %= (10 % 4)`
- `let ready = true`
- `let ok = count == 3`
- `return a + b`
- `return a - b`
- `return a * b`
- `return a / b`
- `return a % b`
- `print("text")`
- `print(123)`
- `print(1 + 2)`
- `print((1 + 2))`
- `print(5 - 2)`
- `print(2 * 3)`
- `print(2 + 3 * 4)`
- `print(8 / 2)`
- `print(8 + 6 / 2)`
- `print(7 % 3)`
- `print(8 + 7 % 3)`
- `print(true)`
- `print(1 < 2)`
- `print(name)`
- `print(add(1, 2))`
- `if ready { ... }`
- `if (ready) { ... }`
- `if is_ready(count) { ... }`
- `if 1 < 2 { ... }`
- `if false { ... } else { ... }`
- `if false { ... } else if true { ... } else { ... }`
- `while count < 3 { ... }`
- `for i from 0 to 3 { ... }`
- `for i from 0 to 6 step 2 { ... }`
- `for i from 0 through 3 { ... }`
- `for step` 的 `step` 必须是 `int`，显式 `step 0` 会报错
- 除法右侧如果是显式静态 `0` 或 `(0)` 会报 `division by zero`
- `/=` 右侧如果是显式静态 `0` 或 `(0)` 会报 `division by zero`
- 取模右侧如果是显式静态 `0` 或 `(0)` 会报 `modulo by zero`
- `%=` 右侧如果是显式静态 `0` 或 `(0)` 会报 `modulo by zero`
- 返回值函数中的循环体可写 `return count`，但函数末尾仍需要兜底 `return`
- `break`
- `continue`
- 基础语义/类型检查：`string`、`int`、`bool`
- 兼容保留：`fn`、`main`、`let`、`print` 暂时可作为变量名或参数名；`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`true`、`false` 不作为普通名字使用。
- AST 节点模块：`lai_ast.py`
- 共享核心：`lai_core.py`
- 语义/类型检查：`lai_checker.py`
- 通用后端描述符：`lai_backend.py`
- C 后端和 `clang` 构建：`lai_c_backend.py`
- 内部标准库/运行时 C 输出辅助：`lai_stdlib.py`
- 括号表达式 AST：`GroupExpr`
- 减法表达式 AST：`SubtractExpr`
- 乘法表达式 AST：`MultiplyExpr`
- 除法表达式 AST：`DivideExpr`
- 取模表达式 AST：`ModuloExpr`
- 减法赋值语句 AST：`MinusAssignStmt`
- 乘法赋值语句 AST：`MultiplyAssignStmt`
- 除法赋值语句 AST：`DivideAssignStmt`
- 取模赋值语句 AST：`ModuloAssignStmt`

当前不支持：

- `main` 返回类型
- 通用 `return` 早退，例如循环外的非最终 `if { return ... }`
- `while true { return ... }` 作为保证返回路径
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++`
- 浮点数、动态运行时除零检查、负数和完整运算符优先级
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 变量类型声明
- 完整类型推导
- 缩进块语法
- 完整 LLVM 后端：实验性 LLVM 文本 IR 只支持空 `main` 或顶层 `print` 中的 `IntExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；变量、赋值、比较、布尔、字符串、控制流和用户函数会报明确能力错误
- GC、JIT、并发、包管理、标准库

不要把远期设计文档里的能力写成“已经实现”。需要新增语言能力时，先更新设计或计划，再改代码和测试。

## 开发命令

运行单元测试：

```powershell
python -m unittest discover -v
```

运行端到端示例：

```powershell
python lai_compiler.py main.ly --run
```

运行实验性 LLVM 示例：

```powershell
python lai_compiler.py examples/unary_integer.ly --run
python lai_compiler.py examples/unary_integer.ly --backend llvm --run
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
```

`--backend {c,llvm}` 默认选择 `c`。v0.34 支持前缀 `+expr` 和 `-expr`，由 `UnaryExpr` 表示；优先级是分组/基础表达式、一元、乘除取模、加减、比较。源码 `int` 范围为 `-2147483648..2147483647`，静态拒绝零除数、一元 `INT_MIN` 溢出和 `for step <= 0`。动态运行时溢出与动态非正 step 仍不检查。实验性 LLVM 仅在原有顶层整数 `print` 子集中加入 `UnaryExpr`：一元 `+` 透传，一元 `-` 生成 `sub i32 0, value` 或 `INT_MIN` 常量；变量、赋值、比较、布尔、字符串、控制流和用户函数仍不支持。下一步是 v0.35 完善基础比较能力，具体语法集合仍需用户选择。

如果 `clang` 不在 `Path` 中，端到端编译可能失败；优先使用已经配置好 LLVM/MSVC
环境的终端。

## 文件约定

- `lai_compiler.py` 是 v0 编译器入口，保留 lexer、parser、文件编译和 CLI；解析和检查后默认委托 `C_BACKEND`。
- `lai_ast.py` 提供 AST 节点，新增语法节点优先放这里。
- `lai_core.py` 提供共享错误类型和核心名称规则。
- `lai_checker.py` 提供语义/类型检查。
- `lai_backend.py` 提供不可变的通用 `Backend` 描述符。
- `lai_clang.py` 提供共享 `clang` 调用和既有错误措辞。
- `lai_c_backend.py` 提供完整默认 C 后端代码生成和构建。
- `lai_llvm_backend.py` 提供不依赖 `llvmlite` 的实验性文本 LLVM IR 后端。
- `lai_stdlib.py` 是 v0.7 的内部标准库/运行时 C 输出辅助模块。
- `tests/test_lai_compiler.py` 覆盖翻译和错误处理行为。
- `tests/test_lai_ast.py` 覆盖 AST 节点和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖标准库辅助模块。
- `tests/test_lai_clang.py` 覆盖共享 clang 调用和错误行为。
- `tests/test_lai_llvm_backend.py` 覆盖实验性 LLVM 文本 IR 能力边界。
- `main.ly` 是最小示例程序。
- `examples/unary_integer.ly` 可由 C 和 LLVM 后端运行；`examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly` 是可运行 LLVM 示例；`examples/build/*.ll` 和 `*.exe` 是生成的未跟踪输出。
- `build/` 是生成目录，不要把 `build/main.c` 当作手写源文件维护。
- `hello.c`、`hello.exe` 看起来是早期实验文件，除非任务明确要求，不要围绕它们扩展。
- `docs/ai/` 是给未来 AI/agent 接手用的项目记忆，改动项目行为时要同步更新。

## 修改原则

- 保持 v0 小而清楚，避免一次性引入大型语言架构。
- 任何语法或错误行为变化都应补对应测试。
- 新增用户可见语法时，先给出 2-3 个有意义候选、示例、利弊、与 LAI 一致性、成熟语言实践和明确推荐，由用户选择；内部重构不制造虚假语法选项。
- 生成 C 代码时优先使用简单、可读、可测试的字符串输出；等语言范围扩大后再考虑 AST/IR 分层。
- 不要回滚用户已有改动；如果看到不相关文件变化，先保留。
