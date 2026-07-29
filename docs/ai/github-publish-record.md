# GitHub 发布记录

最后更新：2026-07-29

## 仓库与分支

- GitHub：`https://github.com/pilipalaBeng/AIProgrammingLanguage`
- Remote：`origin https://github.com/pilipalaBeng/AIProgrammingLanguage.git`
- 主分支：`main -> origin/main`

本文只记录已经真实提交并推送的发布事实。当前能力以源码、测试、`README.md` 和
`docs/ai/active-context.md` 为准；不要根据未来路线图推断已实现能力。

## v0.38 发布记录

v0.38 通用函数早退由三次逻辑提交实现并发布：

```text
f79e275 feat(checker): 支持通用函数早退和不可达检查
eb48ad1 feat(checker): 分析静态无限循环返回路径
e352e3d docs(v0.38): 完成通用函数早退发布闭环
```

Task 3 发布提交的完整 hash：

```text
e352e3dd7405e627ee9d538cfade49573a21fdfe
```

`e352e3d` 已于 2026-07-29 推送到 `origin/main`。该发布基线包含：

- 返回值函数中的 guard clause、嵌套分支和循环路径 `return expr`。
- 第一条不可达语句诊断，以及所有可达路径必须返回的检查。
- 仅识别字面量 `true` 及其括号形式的最小静态 `while true` 返回证明。
- `examples/general_early_return.ly`、CLI v0.38 说明、项目文档和六篇本地知识文档。
- 有道云 `学习/开发/语言开发/灵语（LAI）` 下六篇同名笔记的同步和重载回读。

本版没有新增 token、parser 规则、AST 节点或后端 lowering。C 后端保持完整默认路径；
实验性 LLVM 仍不支持用户函数和控制流。

## 发布验证

`e352e3d` 提交前已完成：

```powershell
python -m unittest discover -v
python lai_compiler.py main.ly --run
python lai_compiler.py examples/basic_comparisons.ly --run
python lai_compiler.py examples/boolean_logic.ly --run
python lai_compiler.py examples/runtime_integer_safety.ly --run
python lai_compiler.py examples/general_early_return.ly --run
python lai_compiler.py examples/unary_integer.ly --run
python lai_compiler.py examples/unary_integer.ly --backend llvm --run
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
git diff --check
```

结果：399 项单元测试通过；v0.38 C 示例依次输出 `-1`、`0`、`1`、`7`、`8`；
同一示例使用 LLVM 时按预期以退出码 1 报：

```text
LAI compile error: line 1: LLVM backend does not support FunctionDef yet
```

Task 3 独立审查者重新执行了完整测试和关键 C/LLVM 验证，结论为 `READY`，没有阻塞或重要问题。

最终全版本审查者随后从 v0.38 计划基线复核到发布记录，独立运行 399 项测试和关键后端验证，
确认控制流语义、诊断顺序、文档事实与远端提交一致，结论为 `READY_TO_CLOSE`。

## 生成物边界

`.gitignore` 的 `build/` 规则覆盖根目录和 `examples/build/` 下生成的 `.c`、`.ll`、`.exe`；
这些文件不属于发布源码，不应手工维护或提交。`.superpowers/sdd/` 是本地审查工作区，也不提交。

## 下一步

当前版本是 v0.38。下一版是 v0.39 数组核心；剩余编号队列为 v0.39-v0.44，共 6 个版本。
数组语法尚未确定，也尚未实现。新增用户可见语法前，必须先给出候选方案并由用户确认。

## 历史首次发布

```text
67271e2 Add LAI v0 compiler
77ff631 Add project README
```

这两个提交记录了最早的编译器和 README 发布；它们不代表当前版本能力。
