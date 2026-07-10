# AGENTS.md

## 项目定位

这个仓库是 LAI（灵语）v0 编译器原型。当前目标很小：把一个极简 `.ly`
程序经过基础语义/类型检查后翻译成 C，再通过 `clang` 编译成 Windows 可执行文件。

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
5. `docs/superpowers/specs/2026-07-10-lai-v0.22-parenthesized-expressions-design.md`
6. `docs/superpowers/plans/2026-07-10-lai-v0.22-parenthesized-expressions.md`
7. `docs/superpowers/specs/2026-07-10-lai-v0.21-through-loop-design.md`
8. `docs/superpowers/plans/2026-07-10-lai-v0.21-through-loop.md`
9. `docs/superpowers/specs/2026-07-10-lai-v0.20-for-step-design.md`
10. `docs/superpowers/plans/2026-07-10-lai-v0.20-for-step.md`
11. `docs/superpowers/specs/2026-07-09-lai-v0.19-plus-assign-design.md`
12. `docs/superpowers/plans/2026-07-09-lai-v0.19-plus-assign.md`
13. `docs/superpowers/specs/2026-07-09-lai-v0.18-for-loop-design.md`
14. `docs/superpowers/plans/2026-07-09-lai-v0.18-for-loop.md`
15. `docs/superpowers/specs/2026-07-09-lai-v0.17-loop-return-flow-design.md`
16. `docs/superpowers/plans/2026-07-09-lai-v0.17-loop-return-flow.md`
17. `docs/superpowers/specs/2026-07-09-lai-v0.16-break-continue-design.md`
18. `docs/superpowers/plans/2026-07-09-lai-v0.16-break-continue.md`
19. `docs/superpowers/specs/2026-07-09-lai-v0.15-while-assignment-design.md`
20. `docs/superpowers/plans/2026-07-09-lai-v0.15-while-assignment.md`
21. `docs/superpowers/specs/2026-07-09-lai-v0.14-branch-return-flow-design.md`
22. `docs/superpowers/plans/2026-07-09-lai-v0.14-branch-return-flow.md`
23. `docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md`
24. `docs/superpowers/plans/2026-07-06-lai-v0-compiler.md`

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
- `let count = add(1, 2)`
- `count = count + 1`
- `count += 1`
- `let ready = true`
- `let ok = count == 3`
- `return a + b`
- `print("text")`
- `print(123)`
- `print(1 + 2)`
- `print((1 + 2))`
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
- 返回值函数中的循环体可写 `return count`，但函数末尾仍需要兜底 `return`
- `break`
- `continue`
- 基础语义/类型检查：`string`、`int`、`bool`
- 兼容保留：`fn`、`main`、`let`、`print` 暂时可作为变量名或参数名；`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`true`、`false` 不作为普通名字使用。
- AST 节点模块：`lai_ast.py`
- 共享核心：`lai_core.py`
- 语义/类型检查：`lai_checker.py`
- C 后端：`lai_c_backend.py`
- 内部标准库/运行时 C 输出辅助：`lai_stdlib.py`
- 括号表达式 AST：`GroupExpr`

当前不支持：

- `main` 返回类型
- 通用 `return` 早退，例如循环外的非最终 `if { return ... }`
- `while true { return ... }` 作为保证返回路径
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++` 和 `-=`, `*=`, `/=` 等其他复合赋值
- 普通减法、乘法、除法、负数和完整运算符优先级
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 变量类型声明
- 完整类型推导
- 缩进块语法
- LLVM IR 后端
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

如果 `clang` 不在 `Path` 中，端到端编译可能失败；优先使用已经配置好 LLVM/MSVC
环境的终端。

## 文件约定

- `lai_compiler.py` 是 v0 编译器入口，保留 lexer、parser、文件编译和 CLI。
- `lai_ast.py` 提供 AST 节点，新增语法节点优先放这里。
- `lai_core.py` 提供共享错误类型和核心名称规则。
- `lai_checker.py` 提供语义/类型检查。
- `lai_c_backend.py` 提供 C 后端代码生成。
- `lai_stdlib.py` 是 v0.7 的内部标准库/运行时 C 输出辅助模块。
- `tests/test_lai_compiler.py` 覆盖翻译和错误处理行为。
- `tests/test_lai_ast.py` 覆盖 AST 节点和兼容导出入口。
- `tests/test_lai_module_boundaries.py` 覆盖拆分模块和兼容导出入口。
- `tests/test_lai_stdlib.py` 覆盖标准库辅助模块。
- `main.ly` 是最小示例程序。
- `build/` 是生成目录，不要把 `build/main.c` 当作手写源文件维护。
- `hello.c`、`hello.exe` 看起来是早期实验文件，除非任务明确要求，不要围绕它们扩展。
- `docs/ai/` 是给未来 AI/agent 接手用的项目记忆，改动项目行为时要同步更新。

## 修改原则

- 保持 v0 小而清楚，避免一次性引入大型语言架构。
- 任何语法或错误行为变化都应补对应测试。
- 生成 C 代码时优先使用简单、可读、可测试的字符串输出；等语言范围扩大后再考虑 AST/IR 分层。
- 不要回滚用户已有改动；如果看到不相关文件变化，先保留。
