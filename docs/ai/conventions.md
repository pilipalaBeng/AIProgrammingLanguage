# 项目约定

最后更新：2026-07-06

## 语言约定

当前 v0.3 语法保持极小：

```lai
fn main() {
    // comment
    print("Hello LAI")
    let count = 1 + 2
    print(count)
    let ready = count == 3
    if ready {
        print("ready")
    }
}
```

约定：

- v0.3 使用英文关键字：`fn`、`let`、`print`、`if`。
- v0.3 使用 `{}` 表示块。
- 语句以换行结束，不使用分号。
- 注释使用 `//`，从 `//` 到行尾都忽略。
- 字符串使用双引号。
- 整数只支持十进制非负整数。
- 简单表达式当前只支持整数加法：`1 + 2`、`1 + 2 + 3`。
- 布尔字面量为 `true` 和 `false`。
- 比较表达式当前支持 `<`、`>` 和 `==`。
- `if` 当前只支持无 `else` 的最小块语法。
- 当前不支持括号表达式、完整运算符优先级、`else` 或循环。
- 变量名使用 ASCII 字母、数字和 `_`，且不能以数字开头。

远期可以探索缩进块、类型推导、LLVM IR 等能力，但不要提前写进当前行为。

## 编译器代码约定

- 保持 `compile_source(source: str) -> str` 作为测试入口。
- 对用户可见的编译失败抛 `LaiCompileError`。
- 错误信息尽量包含 `line N`。
- 新增语法前先加测试。
- 不为 v0.x 提前引入外部 Python 依赖。
- 当前编译器已在单文件内拆成 lexer、parser、AST 和 C codegen；等文件继续变大时再拆模块。

## 测试约定

核心测试命令：

```powershell
python -m unittest tests.test_lai_compiler -v
```

端到端验证命令：

```powershell
python lai_compiler.py main.lai --run
```

测试优先覆盖：

- 成功生成的关键 C 代码片段。
- 行号化错误。
- 符号表行为，例如未知变量和重复变量。
- 新语法的最小正例和反例。

## 文档约定

- `docs/ai/project-brief.md` 记录项目全局概览。
- `docs/ai/active-context.md` 记录最近上下文和下一步。
- `docs/ai/architecture-map.md` 记录当前架构。
- `docs/ai/module-index.md` 记录文件索引。
- `docs/ai/conventions.md` 记录约定。
- `docs/ai/decisions/` 记录重要决策。
- `docs/ai/session-log/` 记录会话日志。

项目行为变化时，至少同步更新 `active-context.md`；架构变化时同步更新
`architecture-map.md` 和 `module-index.md`。

## 生成物约定

- `build/` 下文件由编译器生成。
- 不要手动维护 `build/main.c`。
- `.exe` 文件只用于本地验证，不代表源代码状态。
