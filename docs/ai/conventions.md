# 项目约定

最后更新：2026-07-09

## 语言约定

当前 v0.16 语法保持极小：

```lai
fn add(a: int, b: int) -> int {
    return a + b
}

fn grade(score: int) -> string {
    if score > 90 {
        return "A"
    } else if score > 80 {
        return "B"
    } else {
        return "C"
    }
}

fn greet(name: string) {
    print(name)
}

fn main() {
    // comment
    greet("hello")
    let count = add(1, 2)
    print(count)
    let loop = 0
    while loop < 5 {
        loop = loop + 1
        if loop < 2 {
            continue
        }
        print(loop)
        if loop > 3 {
            break
        }
    }
    print(count)
    if false {
        print("then")
    } else if true {
        print("middle")
    } else {
        print("else")
    }
}
```

约定：

- v0.16 使用英文关键字：`fn`、`let`、`print`、`if`、`else`、`return`、`while`、`break`、`continue`。
- v0.16 使用 `{}` 表示块。
- v0.16 正式源码扩展名为 `.ly`。
- 旧 `.lai` 文件暂时仍可被编译器读取，但不再作为推荐示例扩展名。
- 顶层可以有多个 `fn`，但必须包含一个 `fn main() { ... }`。
- 用户函数当前支持零个或多个显式类型参数，也支持可选返回类型。
- 函数参数写作 `name: string`、`count: int`、`ready: bool`。
- 函数返回类型写作 `-> int`、`-> string` 或 `-> bool`。
- 带返回值函数必须保证所有路径返回：最后一条顶层语句可以是 `return expr`，也可以是完整 `if / else if / else` 返回分支。
- 函数调用可以作为语句，例如 `greet("JD")`，也可以作为表达式，例如 `let count = add(1, 2)`。
- 已存在变量或参数可以重新赋值，例如 `count = count + 1`；赋值类型必须和原类型一致。
- `main` 函数当前仍必须是 `fn main() { ... }`，不能带参数或返回类型。
- 语句以换行结束，不使用分号。
- 注释使用 `//`，从 `//` 到行尾都忽略。
- 字符串使用双引号。
- 整数只支持十进制非负整数。
- 简单表达式当前支持整数加法：`1 + 2`、`count + 1`、`add(1, 2) + 3`。
- 布尔字面量为 `true` 和 `false`。
- 比较表达式当前支持 `<`、`>` 和 `==`。
- `if` 当前支持可选 `else`，例如 `if ready { ... } else { ... }`。
- 当前支持 `else if` 链，例如 `if a { ... } else if b { ... } else { ... }`。
- 当前支持最小 `while` 循环，例如 `while count < 3 { ... }`。
- 当前支持 `break` 跳出最近一层循环。
- 当前支持 `continue` 进入最近一层循环的下一轮。
- 当前显式检查 `string`、`int`、`bool` 三种基础类型。
- `if` 条件必须是 `bool`。
- `while` 条件必须是 `bool`。
- 加法表达式当前只接受 `int` 操作数。
- 比较表达式当前只接受两个 `int` 操作数，结果是 `bool`。
- 当前不支持 `return` 早退、循环中的 `return` 控制流分析、`for`、带标签的 `break label` / `continue label`、`count++`、`count += 1`、默认参数、命名参数、可变参数、函数重载、括号表达式、完整运算符优先级或单词关键字 `elseif`。
- 变量名和参数名使用 ASCII 字母、数字和 `_`，且不能以数字开头。
- 为保持旧示例兼容，`fn`、`main`、`let`、`print` 暂时仍可作为变量名或参数名；`if`、`else`、`return`、`true`、`false` 不作为普通名字使用。

远期可以探索缩进块、类型推导、LLVM IR 等能力，但不要提前写进当前行为。

## 编译器代码约定

- 保持 `compile_source(source: str) -> str` 作为测试入口。
- 对用户可见的编译失败抛 `LaiCompileError`。
- 错误信息尽量包含 `line N`。
- 新增语法前先加测试。
- 不为 v0.x 提前引入外部 Python 依赖。
- 当前 `lai_compiler.py` 保留 lexer、parser、文件编译和 CLI。
- `lai_ast.py` 负责 AST 节点定义，新增语法节点优先放这里。
- `lai_checker.py` 负责语义/类型检查。
- `lai_c_backend.py` 负责 C 后端。
- `lai_stdlib.py` 只放内部标准库/运行时 C 输出辅助，不代表已经有用户可直接调用的标准库 API。

## 测试约定

核心测试命令：

```powershell
python -m unittest discover -v
```

端到端验证命令：

```powershell
python lai_compiler.py main.ly --run
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
