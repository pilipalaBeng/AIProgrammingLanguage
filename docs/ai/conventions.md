# 项目约定

最后更新：2026-07-10

## 语言约定

当前 v0.29 语法保持极小：

```lai
fn add(a: int, b: int) -> int {
    return a + b
}

fn diff(a: int, b: int) -> int {
    return a - b
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

fn first_over_two(limit: int) -> int {
    let count = 0
    while count < limit {
        if count > 2 {
            return count
        }
        count += 1
    }
    return limit
}

fn show_basic_demo() {
    greet("hello")
    let count = (add(1, 2))
    let reduced = count - 1
    reduced -= 1
    let multiplied = 2 + 3 * 4
    multiplied *= 2
    let divided = multiplied / 2
    divided /= 2
    let remainder = 7 % 3
    print(count)
    print(reduced)
    print(multiplied)
    print(divided)
    print(remainder)
    print(diff(5, 2))
    print(first_over_two(5))
}

fn show_for_demo() {
    for i from 0 to 3 {
        print(i)
    }
    for even from 0 to 6 step 2 {
        print(even)
    }
    for closed from 0 through 3 {
        print(closed)
    }
}

fn show_loop_control_demo() {
    let loop = 0
    while loop < 5 {
        loop += 1
        if loop < 2 {
            continue
        }
        print(loop)
        if loop > 3 {
            break
        }
    }
}

fn show_condition_demo() {
    if (false) {
        print("then")
    } else if true {
        print("middle")
    } else {
        print("else")
    }
}

fn main() {
    // comment
    show_basic_demo()
    show_for_demo()
    show_loop_control_demo()
    show_condition_demo()
}
```

约定：

- v0.29 使用英文关键字：`fn`、`let`、`print`、`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`。
- v0.29 使用 `{}` 表示块。
- v0.29 正式源码扩展名为 `.ly`。
- 旧 `.lai` 文件暂时仍可被编译器读取，但不再作为推荐示例扩展名。
- 顶层可以有多个 `fn`，但必须包含一个 `fn main() { ... }`。
- 用户函数当前支持零个或多个显式类型参数，也支持可选返回类型。
- 函数参数写作 `name: string`、`count: int`、`ready: bool`。
- 函数返回类型写作 `-> int`、`-> string` 或 `-> bool`。
- 带返回值函数必须保证所有路径返回：最后一条顶层语句可以是 `return expr`，也可以是完整 `if / else if / else` 返回分支。
- 函数调用可以作为语句，例如 `greet("JD")`，也可以作为表达式，例如 `let count = add(1, 2)`。
- 已存在变量或参数可以重新赋值，例如 `count = count + 1`；赋值类型必须和原类型一致。
- 已存在 `int` 变量或参数可以使用 `+=`、`-=`、`*=` 和 `/=`，例如 `count += 1`、`count -= 1`、`count *= 2`、`count /= 2`；右侧表达式必须是 `int`。
- `main` 函数当前仍必须是 `fn main() { ... }`，不能带参数或返回类型。
- 语句以换行结束，不使用分号。
- 注释使用 `//`，从 `//` 到行尾都忽略。
- 字符串使用双引号。
- 整数只支持十进制非负整数。
- 简单表达式当前支持整数加法、减法、乘法、除法和取模：`1 + 2`、`count + 1`、`add(1, 2) + 3`、`5 - 2`、`count - 1`、`diff(5, 2) - 1`、`2 * 3`、`count * 2`、`8 / 2`、`count / 2`、`7 % 3`、`count % 2`。
- 当前支持最小算术优先级：`*`、`/` 和 `%` 高于 `+` / `-`，例如 `8 + 7 % 3` 按 `8 + (7 % 3)` 处理。
- 当前支持括号表达式，例如 `let count = (1 + 2)`、`print((1 + 2))` 和 `if (ready) { ... }`；括号保留分组，并可覆盖乘除取模优先级，例如 `(10 + 5) % 4`。
- 布尔字面量为 `true` 和 `false`。
- 比较表达式当前支持 `<`、`>` 和 `==`。
- `if` 当前支持可选 `else`，例如 `if ready { ... } else { ... }`。
- 当前支持 `else if` 链，例如 `if a { ... } else if b { ... } else { ... }`。
- 当前支持最小 `while` 循环，例如 `while count < 3 { ... }`。
- 当前支持最小计数 `for` 循环，例如 `for i from 0 to 3 { ... }`；`to` 不包含终点。
- 当前支持正向计数循环步长，例如 `for i from 0 to 6 step 2 { ... }`；省略 `step` 时默认为 `1`。
- 当前支持包含终点计数循环，例如 `for i from 0 through 3 { ... }`；`through` 包含终点。
- 当前支持 `break` 跳出最近一层循环。
- 当前支持 `continue` 进入最近一层循环的下一轮。
- `for` 循环变量是循环体局部 `int`，起点、终点和步长必须是 `int`；显式字面量 `step 0` 会报错。
- 返回值函数的循环体内可以写局部 `return`，但函数末尾仍需要兜底 `return` 或完整返回分支。
- 当前显式检查 `string`、`int`、`bool` 三种基础类型。
- `if` 条件必须是 `bool`。
- `while` 条件必须是 `bool`。
- 加法表达式当前只接受 `int` 操作数。
- 减法表达式当前只接受两个 `int` 操作数，结果是 `int`。
- 乘法表达式当前只接受 `int` 操作数，结果是 `int`。
- 除法表达式当前只接受两个 `int` 操作数，结果是 `int`；显式静态 `8 / 0` 和 `8 / (0)` 会报错。
- 取模表达式当前只接受两个 `int` 操作数，结果是 `int`；显式静态 `7 % 0` 和 `7 % (0)` 会报错。
- 除法赋值 `/=` 当前只接受已有 `int` 变量或参数作为目标，右侧值必须是 `int`；显式静态 `count /= 0` 和 `count /= (0)` 会报错。
- 比较表达式当前只接受两个 `int` 操作数，结果是 `bool`。
- 当前不支持通用 `return` 早退、`while true { return ... }` 作为保证返回路径、倒序 `for`、负数步长、`for item in list`、带标签的 `break label` / `continue label`、`count++`、`%=`、浮点数、动态运行时除零检查、负数、默认参数、命名参数、可变参数、函数重载、完整运算符优先级或单词关键字 `elseif`。
- 变量名和参数名使用 ASCII 字母、数字和 `_`，且不能以数字开头。
- 为保持旧示例兼容，`fn`、`main`、`let`、`print` 暂时仍可作为变量名或参数名；`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`true`、`false` 不作为普通名字使用。

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
