# AGENTS.md

## 项目定位

这个仓库是 LAI（灵语）v0.40 第一阶段编译器原型。当前目标很小：把一个极简 `.ly`
程序经过语义、类型和控制流检查后默认翻译成 C，再通过 `clang` 编译成 Windows 可执行文件；仍保留受限的实验性文本 LLVM IR 路径。第一阶段仅新增数组元素修改，长度 API 和遍历仍在 v0.40 待实现。

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

当前 v0.40 第一阶段设计与计划优先于下列历史版本入口：

- `docs/superpowers/specs/2026-09-07-lai-v0.40-array-element-assignment-design.md`
- `docs/superpowers/plans/2026-09-07-lai-v0.40-array-element-assignment.md`

v0.39 数组核心设计与计划：

- `docs/superpowers/specs/2026-09-05-lai-v0.39-local-arrays-design.md`
- `docs/superpowers/plans/2026-09-05-lai-v0.39-local-arrays.md`

1. `docs/ai/active-context.md`
2. `docs/ai/project-brief.md`
3. `docs/ai/architecture-map.md`
4. `docs/ai/conventions.md`
5. `docs/superpowers/specs/2026-07-29-lai-v0.38-general-early-return-design.md`
6. `docs/superpowers/plans/2026-07-29-lai-v0.38-general-early-return.md`
7. `docs/superpowers/specs/2026-07-28-lai-v0.37-runtime-integer-safety-design.md`
8. `docs/superpowers/plans/2026-07-28-lai-v0.37-runtime-integer-safety.md`
9. `docs/superpowers/specs/2026-07-28-lai-v0.35-basic-comparisons-design.md`
10. `docs/superpowers/plans/2026-07-28-lai-v0.35-basic-comparisons.md`
11. `docs/superpowers/specs/2026-07-23-lai-v0.34-unary-integer-expressions-design.md`
12. `docs/superpowers/plans/2026-07-23-lai-v0.34-unary-integer-expressions.md`
13. `docs/superpowers/specs/2026-07-23-lai-v0.33-llvm-integer-arithmetic-design.md`
14. `docs/superpowers/plans/2026-07-23-lai-v0.33-llvm-integer-arithmetic.md`
15. `docs/superpowers/specs/2026-07-11-lai-v0.32-textual-llvm-backend-design.md`
16. `docs/superpowers/plans/2026-07-13-lai-v0.32-textual-llvm-backend.md`
17. `docs/superpowers/specs/2026-07-11-lai-v0.31-backend-boundary-design.md`
18. `docs/superpowers/plans/2026-07-11-lai-v0.31-backend-boundary.md`
19. `docs/superpowers/specs/2026-07-11-lai-v0.30-modulo-assign-design.md`
20. `docs/superpowers/plans/2026-07-11-lai-v0.30-modulo-assign.md`
21. `docs/superpowers/specs/2026-07-10-lai-v0.29-modulo-expressions-design.md`
22. `docs/superpowers/plans/2026-07-10-lai-v0.29-modulo-expressions.md`
23. `docs/superpowers/specs/2026-07-10-lai-v0.28-divide-assign-design.md`
24. `docs/superpowers/plans/2026-07-10-lai-v0.28-divide-assign.md`
25. `docs/superpowers/specs/2026-07-10-lai-v0.27-division-expressions-design.md`
26. `docs/superpowers/plans/2026-07-10-lai-v0.27-division-expressions.md`
27. `docs/superpowers/specs/2026-07-10-lai-v0.26-multiply-assign-design.md`
28. `docs/superpowers/plans/2026-07-10-lai-v0.26-multiply-assign.md`
29. `docs/superpowers/specs/2026-07-10-lai-v0.25-multiplication-expressions-design.md`
30. `docs/superpowers/plans/2026-07-10-lai-v0.25-multiplication-expressions.md`
31. `docs/superpowers/specs/2026-07-10-lai-v0.24-minus-assign-design.md`
32. `docs/superpowers/plans/2026-07-10-lai-v0.24-minus-assign.md`
33. `docs/superpowers/specs/2026-07-10-lai-v0.23-subtraction-expressions-design.md`
34. `docs/superpowers/plans/2026-07-10-lai-v0.23-subtraction-expressions.md`
35. `docs/superpowers/specs/2026-07-10-lai-v0.22-parenthesized-expressions-design.md`
36. `docs/superpowers/plans/2026-07-10-lai-v0.22-parenthesized-expressions.md`
37. `docs/superpowers/specs/2026-07-10-lai-v0.21-through-loop-design.md`
38. `docs/superpowers/plans/2026-07-10-lai-v0.21-through-loop.md`
39. `docs/superpowers/specs/2026-07-10-lai-v0.20-for-step-design.md`
40. `docs/superpowers/plans/2026-07-10-lai-v0.20-for-step.md`
41. `docs/superpowers/specs/2026-07-09-lai-v0.19-plus-assign-design.md`
42. `docs/superpowers/plans/2026-07-09-lai-v0.19-plus-assign.md`
43. `docs/superpowers/specs/2026-07-09-lai-v0.18-for-loop-design.md`
44. `docs/superpowers/plans/2026-07-09-lai-v0.18-for-loop.md`
45. `docs/superpowers/specs/2026-07-09-lai-v0.17-loop-return-flow-design.md`
46. `docs/superpowers/plans/2026-07-09-lai-v0.17-loop-return-flow.md`
47. `docs/superpowers/specs/2026-07-09-lai-v0.16-break-continue-design.md`
48. `docs/superpowers/plans/2026-07-09-lai-v0.16-break-continue.md`
49. `docs/superpowers/specs/2026-07-09-lai-v0.15-while-assignment-design.md`
50. `docs/superpowers/plans/2026-07-09-lai-v0.15-while-assignment.md`
51. `docs/superpowers/specs/2026-07-09-lai-v0.14-branch-return-flow-design.md`
52. `docs/superpowers/plans/2026-07-09-lai-v0.14-branch-return-flow.md`
53. `docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
54. `docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`

如果要了解远期愿景，再读：

- `docs/Document/AI时代极简高性能编程语言设计方案（含专属命名+AI原生优化特性）.md`
- `docs/Document/零基础非从业人员开发灵语（LAI）编程语言：完整工具+系统+落地步骤.md`

## 当前实现边界

`lai_compiler.py` 当前支持：

- `fn main() { ... }`
- `fn greet() { ... }`
- `fn show(name: string, count: int, ready: bool) { ... }`
- `fn add(a: int, b: int) -> int { ... }`
- 返回值函数支持条件、嵌套分支和循环路径中的 `return expr`，包括 guard clause
- 所有可达路径必须返回；首条不可达语句报 `line N: unreachable statement`
- `while true { return ... }` 及括号包裹的 `(true)` 可作为保证返回路径
- `greet()`
- `show("JD", 3, true)`
- `// comment`
- `let name = "text"`
- 显式局部数组声明：`let scores: int[] = [90, 95, 100]`；支持同构固定长度的 `int[]`、`string[]`、`bool[]` 和有类型的空数组 `let empty: int[] = []`
- 数组字面量只用于显式数组声明的直接初始化；元素按从左到右顺序各求值一次，元素内部沿用既有表达式规则
- 索引读取和修改：`scores[index]`，索引必须为从 0 开始的 `int`；编译期可算出的越界报编译错误，动态越界访问前向 `stderr` 输出行号、index、length 并以 `EXIT_FAILURE` 退出
- 三种数组元素支持同型 `=`，仅 `int` 元素支持 `+= -= *= /= %=`；先索引求值及边界检查，再旧值读取（复合赋值），再右值，各阶段单次执行，成功才写入，长度不变
- 元素修改沿用 checked i32 和静态零除检查；索引失败不执行右值，右值或算术失败不写入；修改是语句，不是表达式
- 索引结果是标量，可用于现有表达式、打印、函数标量实参和返回；数组可在函数、分支和循环的局部作用域声明
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
- `let inside = count >= 0`
- `let changed = ready != false`
- `let same_name = name == "JD"`
- `let valid = count > 0 and count < 5`
- `let fallback = false or true`
- `let disabled = not ready`
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
- `int` 只有一种 checked i32 语义：纯静态零除和中间溢出在编译期报错；动态 `+ - *`、一元 `-`、`/`、`%` 和五种复合赋值由 C 运行时检查
- C 运行时失败向 `stderr` 输出带行号诊断并以 `EXIT_FAILURE` 退出；`for` 的 start/end/step 各求值一次，动态 step 必须为正，范围上界可正常完成
- 除法右侧如果是显式静态 `0` 或 `(0)` 会报 `division by zero`
- `/=` 右侧如果是显式静态 `0` 或 `(0)` 会报 `division by zero`
- 取模右侧如果是显式静态 `0` 或 `(0)` 会报 `modulo by zero`
- `%=` 右侧如果是显式静态 `0` 或 `(0)` 会报 `modulo by zero`
- 返回值函数中的循环体可写 `return count`；普通 `while` / `for` 仍保守要求循环外兜底，静态 `while true` 可做最小保证返回证明
- `break`
- `continue`
- 基础语义/类型检查：`string`、`int`、`bool`
- 基础比较运算符：`<`、`<=`、`>`、`>=`、`==`、`!=`
- 大小比较只接受两个 `int`；相等比较接受同类型的 `int`、`bool` 或 `string`
- 字符串 `==` / `!=` 由 C 后端生成 `strcmp(...) == 0` / `!= 0`
- 布尔逻辑：`and`、`or`、`not` 只接受 `bool` operand 并返回 `bool`，不支持 truthiness
- 逻辑优先级：比较高于 `not`，`not` 高于 `and`，`and` 高于 `or`
- `and` / `or` 从左到右短路；C 后端生成保留 AST 括号的 `!`、`&&`、`||`
- 兼容保留：`fn`、`main`、`let`、`print` 暂时可作为变量名或参数名；`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`true`、`false`、`and`、`or`、`not` 不作为普通名字使用。
- AST 节点模块：`lai_ast.py`
- 数组 AST：`ArrayExpr`、`IndexExpr`、`IndexAssignStmt(target, operator, value, line)`；`LetStmt.type_name` 默认 `None`，保留旧构造兼容
- 局部数组类型信息：`lai_types.py` 的 `ArrayType(element_type, length)`
- 共享核心：`lai_core.py`
- 语义/类型检查：`lai_checker.py`
- 通用后端描述符：`lai_backend.py`
- C 后端和 `clang` 构建：`lai_c_backend.py`
- 内部标准库/运行时 C 输出辅助：`lai_stdlib.py`
- 括号表达式 AST：`GroupExpr`
- 一元表达式 AST：`UnaryExpr`
- 减法表达式 AST：`SubtractExpr`
- 乘法表达式 AST：`MultiplyExpr`
- 除法表达式 AST：`DivideExpr`
- 取模表达式 AST：`ModuloExpr`
- 逻辑非 AST：`LogicalNotExpr`
- 逻辑与/或 AST：`LogicalExpr`
- 减法赋值语句 AST：`MinusAssignStmt`
- 乘法赋值语句 AST：`MultiplyAssignStmt`
- 除法赋值语句 AST：`DivideAssignStmt`
- 取模赋值语句 AST：`ModuloAssignStmt`

当前不支持：

- `main` 返回类型
- bare `return`、无返回值函数或 `main` 中的 `return`
- 一般常量条件折叠、静态非空 `for` 证明、完整 CFG 和不可达 warning 模式
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++`
- 浮点数、动态整数范围分析、动态非正 `for step` 的恢复、反向循环和完整运算符优先级
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 通用标量变量类型声明；当前局部类型标注仅支持上述三种一维数组类型
- 隐式数组类型、长度 API、数组遍历、方法、切片和多维数组
- 数组参数/返回、整数组复制/赋值/比较/打印；数组参数/返回和整数组复制/赋值已登记为未编号后续候选，不承诺具体版本
- 完整类型推导
- 缩进块语法
- 布尔逻辑符号别名 `&&` / `||` / `!` 和非 `bool` truthiness
- 比较链，例如 `1 < 2 < 3`
- 字符串大小排序比较
- 完整 LLVM 后端：实验性 LLVM 文本 IR 只支持空 `main` 或顶层 `print` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；变量、赋值、比较、`LogicalNotExpr`、`LogicalExpr`、布尔、字符串、控制流和用户函数会报明确能力错误
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
python lai_compiler.py examples/basic_comparisons.ly --run
python lai_compiler.py examples/boolean_logic.ly --run
python lai_compiler.py examples/runtime_integer_safety.ly --run
python lai_compiler.py examples/general_early_return.ly --run
python lai_compiler.py examples/local_arrays.ly --run
python lai_compiler.py examples/array_element_assignment.ly --run
```

运行实验性 LLVM 示例：

```powershell
python lai_compiler.py examples/unary_integer.ly --run
python lai_compiler.py examples/unary_integer.ly --backend llvm --run
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
```

`--backend {c,llvm}` 默认选择 `c`。v0.40 第一阶段新增数组元素修改，沿用 checked i32 和 v0.38 的 `FlowOutcome` 控制流规则。`examples/array_element_assignment.ly` 的 C 输出为 `85`、`60`、`10`、`after`、`1`；`examples/local_arrays.ly` 仍输出 `95`、`LAI`、`1`，`bool` 沿用数字打印。实验性 LLVM 范围不变，main 内有效数组声明会报 `LLVM backend does not support LetStmt yet`；含用户函数的示例也可能先报 `FunctionDef` 能力错误。

2026-09-05 验证结果：数组语义/真实 `clang` 运行测试 27 项通过，数组 AST/解析测试 23 项通过；完整回归 `python -m unittest discover -q` 和最终 `python -m unittest discover -v` 均为 449 项通过，无 skip。CLI help 已更新为 v0.39，对应测试完成先失败后通过验证。全部既有 C/LLVM 示例验证通过；数组示例 LLVM 按预期 exit 1，报 `LAI compile error: line 1: LLVM backend does not support FunctionDef yet`，纯 main 数组单测明确验证 `LetStmt` 能力错误。逐项输出见 `docs/ai/active-context.md` 的 v0.39 验证记录。

当前仅 v0.40 第一阶段元素修改已实现；只读长度和遍历仍在 v0.40 待实现，不代表 v0.40 全量完成。之后为 v0.41 多维数组、v0.42 反向循环、v0.43 字符串/最小用户标准库、v0.44 浮点数、v0.45 LLVM 变量模型与语义复盘。尚有工作的编号队列为 v0.40-v0.45，共 6 个版本；多维数组不顺延，也不代表已经实现。第一阶段验证记录见 `docs/ai/active-context.md`，不得沿用历史测试总数。

2026-09-07 验证：最终完整 `python -m unittest discover -q` 和 `python -m unittest discover -v` 均为 480 项通过、无 skip；CLI help v0.40 测试先失败后通过，新示例默认 C 与严格 C11 / `-O2` 输出一致，LLVM 按预期拒绝。独立审查未发现真实缺陷、回归或阻塞缺口。

如果 `clang` 不在 `Path` 中，端到端编译可能失败；优先使用已经配置好 LLVM/MSVC
环境的终端。

## 文件约定

- `lai_compiler.py` 是 v0 编译器入口，保留 lexer、parser、文件编译和 CLI；解析和检查后默认委托 `C_BACKEND`。
- `lai_ast.py` 提供 AST 节点，新增语法节点优先放这里。
- `lai_core.py` 提供共享错误类型和核心名称规则。
- `lai_types.py` 提供不可变 `ArrayType`、数组类型集合和局部数组索引目标解析辅助。
- `lai_checker.py` 提供语义/类型检查。
- `lai_backend.py` 提供不可变的通用 `Backend` 描述符。
- `lai_clang.py` 提供共享 `clang` 调用和既有错误措辞。
- `lai_c_backend.py` 提供完整默认 C 后端代码生成和构建。
- `lai_llvm_backend.py` 提供不依赖 `llvmlite` 的实验性文本 LLVM IR 后端。
- `lai_stdlib.py` 是 v0.7 的内部标准库/运行时 C 输出辅助模块。
- `tests/test_lai_compiler.py` 覆盖翻译和错误处理行为。
- `tests/test_lai_flow.py` 覆盖通用早退、不可达诊断、循环控制流和所有路径返回。
- `tests/test_lai_array_parser.py` 覆盖数组 AST、类型声明、字面量、索引读取和元素修改解析。
- `tests/test_lai_array_assignment.py`、`tests/test_lai_array_assignment_runtime.py` 覆盖元素修改语义、C 生成和真实 `clang` 的顺序、单次求值及失败行为。
- `tests/test_lai_arrays.py` 覆盖数组语义、类型/静态边界、标量复用和 LLVM 能力边界。
- `tests/test_lai_array_runtime.py` 使用真实 `clang` 覆盖动态边界、初始化顺序、索引单次求值和短路。
- `tests/test_lai_ast.py` 覆盖 AST 节点和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖标准库辅助模块。
- `tests/test_lai_clang.py` 覆盖共享 clang 调用和错误行为。
- `tests/test_lai_llvm_backend.py` 覆盖实验性 LLVM 文本 IR 能力边界。
- `main.ly` 是最小示例程序。
- `examples/local_arrays.ly` 是 v0.39 局部数组 C 示例，实际输出 `95`、`LAI`、`1`。
- `examples/array_element_assignment.ly` 是 v0.40 第一阶段元素修改 C 示例，实际输出 `85`、`60`、`10`、`after`、`1`。
- `examples/basic_comparisons.ly` 是可运行 C 比较示例；`examples/boolean_logic.ly` 是逻辑 C 示例；`examples/runtime_integer_safety.ly` 是动态安全运算与 i32 上界范围 C 示例；`examples/general_early_return.ly` 是 v0.38 通用早退 C 示例；`examples/unary_integer.ly` 可由 C 和 LLVM 后端运行；`examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly` 是可运行 LLVM 示例；`examples/build/*.ll` 和 `*.exe` 是生成的未跟踪输出。
- `build/` 是生成目录，不要把 `build/main.c` 当作手写源文件维护。
- `hello.c`、`hello.exe` 看起来是早期实验文件，除非任务明确要求，不要围绕它们扩展。
- `docs/ai/` 是给未来 AI/agent 接手用的项目记忆，改动项目行为时要同步更新。

## 知识库同步

- 每个用户可见版本或重要架构变更完成并验证后，先汇总本版本最新开发文档，再更新
  `docs/knowledge-base/学习/开发/语言开发/灵语（LAI）/` 中受影响的同名知识文档。
- 本地知识文档更新后，同步上传到有道云笔记
  `学习/开发/语言开发/灵语（LAI）` 的同名笔记；网页端目录和文件名应与本地知识库保持一致。
- 知识库同时面向 AI 检索和开发者阅读：索引应提供事实优先级、快速入口和推荐阅读顺序，主题笔记应保持单一职责。
- 只归档已经由当前源码、配置或测试验证的稳定内容；未来规划和已完成设计但尚未实现的能力必须明确标记为“未实现”。
- 不上传构建产物、临时日志、密钥、个人信息或未经验证的推测。
- 如果有道云未登录、网页不可用或上传验证失败，必须在交付结果中明确记录未完成同步及原因，不得假装已经上传。

## 修改原则

- 保持 v0 小而清楚，避免一次性引入大型语言架构。
- 任何语法或错误行为变化都应补对应测试。
- 新增用户可见语法时，先给出 2-3 个有意义候选、示例、利弊、与 LAI 一致性、成熟语言实践和明确推荐，由用户选择；内部重构不制造虚假语法选项。
- 生成 C 代码时优先使用简单、可读、可测试的字符串输出；等语言范围扩大后再考虑 AST/IR 分层。
- 不要回滚用户已有改动；如果看到不相关文件变化，先保留。
