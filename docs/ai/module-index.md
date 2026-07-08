# 模块索引

最后更新：2026-07-08

## 源码与测试

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `lai_compiler.py` | 编译器主体 | 解析 LAI v0.7，执行基础语义/类型检查，生成 C，调用 `clang`，提供 CLI。 |
| `lai_stdlib.py` | 标准库辅助 | 内部标准库/运行时 C 输出辅助，管理 C preamble、字符串转义和 `print` 输出格式。 |
| `main.ly` | 示例输入 | 最小 LAI 程序，用于端到端验证。 |
| `tests/test_lai_compiler.py` | 单元测试 | 测试 `compile_source`、`check_program` 的生成结果、函数调用、类型检查和错误处理。 |
| `tests/test_lai_stdlib.py` | 单元测试 | 测试内部标准库辅助模块。 |
| `tests/__init__.py` | 测试包标记 | 让 `python -m unittest tests.test_lai_compiler -v` 可稳定导入。 |

## 生成文件

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `build/main.c` | 生成 C | 由 `python lai_compiler.py main.ly --run` 生成。 |
| `build/main.exe` | 生成可执行文件 | 由 `clang` 编译生成。 |
| `__pycache__/` | Python 缓存 | 运行测试或脚本后生成。 |
| `tests/__pycache__/` | Python 测试缓存 | 运行测试后生成。 |

## 早期实验文件

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `hello.c` | 早期 C 示例 | 不是当前编译流程的源文件。 |
| `hello.exe` | 早期可执行文件 | 不是当前编译流程的源文件。 |

## 文档

| 路径 | 角色 | 说明 |
| --- | --- | --- |
| `AGENTS.md` | agent 工作指南 | 给后续 agent 的项目约束、命令和接手顺序。 |
| `docs/ai/project-brief.md` | 项目简报 | 说明 LAI 当前定位、范围和已实现能力。 |
| `docs/ai/active-context.md` | 当前上下文 | 记录最近状态、下一步和风险。 |
| `docs/ai/roadmap.md` | 版本路线图 | 记录 v0.1 之后的阶段规划和近期边界。 |
| `docs/ai/architecture-map.md` | 架构地图 | 说明数据流、文件职责和拆分信号。 |
| `docs/ai/conventions.md` | 项目约定 | 说明语言、测试、文档和生成物约定。 |
| `docs/ai/decisions/0001-lai-v0-compiler-scope.md` | 决策记录 | 记录 v0 使用 C 后端和极小语法范围的决定。 |
| `docs/ai/session-log/2026-07-06.md` | 会话日志 | 记录 2026-07-06 的项目进展。 |
| `docs/superpowers/specs/2026-07-06-lai-v0-compiler-design.md` | v0 设计 | v0 编译器的设计说明。 |
| `docs/superpowers/plans/2026-07-06-lai-v0-compiler.md` | v0 实施计划 | v0 编译器实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.6-type-checker-design.md` | v0.6 设计 | 基础语义/类型检查阶段的设计说明。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.6-type-checker.md` | v0.6 实施计划 | 基础语义/类型检查阶段的实施步骤。 |
| `docs/superpowers/specs/2026-07-08-lai-v0.7-stdlib-boundary-design.md` | v0.7 设计 | 小型标准库/运行时 C 输出辅助边界设计。 |
| `docs/superpowers/plans/2026-07-08-lai-v0.7-stdlib-boundary.md` | v0.7 实施计划 | 小型标准库/运行时 C 输出辅助边界实施步骤。 |
| `docs/Document/AI时代极简高性能编程语言设计方案（含专属命名+AI原生优化特性）.md` | 远期愿景 | 极简高性能语言的总体设计。 |
| `docs/Document/零基础非从业人员开发灵语（LAI）编程语言：完整工具+系统+落地步骤.md` | 落地路线 | 面向零基础开发者的工具和阶段路线。 |
