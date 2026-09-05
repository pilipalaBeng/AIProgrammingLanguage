# 项目约定

最后更新：2026-09-05

## 语言约定

当前 v0.39 语法保持极小；以下先展示既有标量与控制流，数组规则见后文：

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
    let folded = 29
    folded %= 5
    print(count)
    print(reduced)
    print(multiplied)
    print(divided)
    print(remainder)
    print(folded)
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

- v0.39 使用英文关键字：`fn`、`let`、`print`、`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`and`、`or`、`not`。
- v0.39 使用 `{}` 表示块。
- v0.39 正式源码扩展名为 `.ly`。
- 旧 `.lai` 文件暂时仍可被编译器读取，但不再作为推荐示例扩展名。
- 顶层可以有多个 `fn`，但必须包含一个 `fn main() { ... }`。
- 用户函数当前支持零个或多个显式类型参数，也支持可选返回类型。
- 函数参数写作 `name: string`、`count: int`、`ready: bool`。
- 函数返回类型写作 `-> int`、`-> string` 或 `-> bool`。
- 带返回值函数必须保证所有可达路径返回；条件、嵌套分支和循环路径中都可写 `return expr`，guard clause 后的外层语句仍可达。
- 同一语句块没有 fallthrough 路径后，第一条后续语句报 `line N: unreachable statement`。
- 函数调用可以作为语句，例如 `greet("JD")`，也可以作为表达式，例如 `let count = add(1, 2)`。
- 已存在标量变量或参数可以重新赋值，例如 `count = count + 1`；赋值类型必须和原类型一致，数组不支持整体赋值或下标写入。
- 已存在 `int` 变量或参数可以使用 `+=`、`-=`、`*=`、`/=` 和 `%=`，例如 `count += 1`、`count -= 1`、`count *= 2`、`count /= 2`、`count %= 3`；右侧表达式必须是 `int`。
- `main` 函数当前仍必须是 `fn main() { ... }`，不能带参数或返回类型。
- 语句以换行结束，不使用分号。
- 注释使用 `//`，从 `//` 到行尾都忽略。
- 字符串使用双引号。
- 局部数组必需显式声明，例如 `let scores: int[] = [90, 95, 100]`；只支持 `int[]`、`string[]`、`bool[]`，所有元素必须同类型，长度固定，允许有类型的空数组 `let empty: int[] = []`。
- 数组字面量只能作为显式声明的直接初始化值；初始化元素从左到右各求值一次，不改变元素内部的既有表达式求值规则。
- 读取为 `scores[index]`，索引严格为从 0 开始的 `int`，范围 `0 <= index < length`；后缀索引高于一元运算，允许 `(scores)[0]`。
- 编译期可算出的越界直接报错；动态索引访问前检查，失败向 `stderr` 输出行号、index、length 后 `EXIT_FAILURE`，索引只求值一次并保留逻辑短路。
- 索引结果是标量，复用表达式、打印、函数标量实参和返回；数组可在 main、用户函数、分支和循环的局部作用域声明，但不能逃逸。
- 不支持隐式数组类型、数组参数/返回、整数组复制/赋值/比较/打印、下标写入、长度 API、数组遍历、方法、切片、多维数组或通用标量变量类型标注。
- `bool` 继续按数字输出：`true` 打印 `1`，`false` 打印 `0`。
- `int` 使用有符号 i32 源码范围 `-2147483648..2147483647`；整数 token 保持十进制非负量级，一元 `+` / `-` 由 `UnaryExpr` 组合出正负值。
- `int` 只有一种 checked i32 模式，没有性能或 unchecked 开关；纯静态零除和中间溢出在编译期报错，动态 C 算术失败向 `stderr` 输出行号后以 `EXIT_FAILURE` 退出。
- 简单表达式当前支持整数加法、减法、乘法、除法和取模：`1 + 2`、`count + 1`、`add(1, 2) + 3`、`5 - 2`、`count - 1`、`diff(5, 2) - 1`、`2 * 3`、`count * 2`、`8 / 2`、`count / 2`、`7 % 3`、`count % 2`。
- 当前支持最小算术优先级：`*`、`/` 和 `%` 高于 `+` / `-`，例如 `8 + 7 % 3` 按 `8 + (7 % 3)` 处理。
- 当前支持括号表达式，例如 `let count = (1 + 2)`、`print((1 + 2))` 和 `if (ready) { ... }`；括号保留分组，并可覆盖乘除取模优先级，例如 `(10 + 5) % 4`。
- 布尔字面量为 `true` 和 `false`。
- 比较表达式支持 `<`、`<=`、`>`、`>=`、`==` 和 `!=`；未分组比较链会被 parser 拒绝。
- `if` 当前支持可选 `else`，例如 `if ready { ... } else { ... }`。
- 当前支持 `else if` 链，例如 `if a { ... } else if b { ... } else { ... }`。
- 当前支持最小 `while` 循环，例如 `while count < 3 { ... }`。
- 当前支持最小计数 `for` 循环，例如 `for i from 0 to 3 { ... }`；`to` 不包含终点。
- 当前支持正向计数循环步长，例如 `for i from 0 to 6 step 2 { ... }`；省略 `step` 时默认为 `1`。
- 当前支持包含终点计数循环，例如 `for i from 0 through 3 { ... }`；`through` 包含终点。
- 当前支持 `break` 跳出最近一层循环。
- 当前支持 `continue` 进入最近一层循环的下一轮。
- `for` 循环变量是循环体局部 `int`，起点、终点和步长必须是 `int`；显式字面量 `step 0` 会报错。
- 普通 `while` 和所有 `for` 都保守视为可能不执行，返回值函数通常仍需循环外兜底；只识别字面量 `true` 及括号包裹形式的静态 true 循环证明。
- 发散路径不能满足返回值函数；当前循环的 `break` 转成 fallthrough，嵌套循环发散继续向外传播。
- 当前显式检查 `string`、`int`、`bool` 三种基础类型。
- `if` 条件必须是 `bool`。
- `while` 条件必须是 `bool`。
- 加法表达式当前只接受 `int` 操作数。
- 减法表达式当前只接受两个 `int` 操作数，结果是 `int`。
- 乘法表达式当前只接受 `int` 操作数，结果是 `int`。
- 除法表达式当前只接受两个 `int` 操作数，结果是 `int`；显式静态 `8 / 0` 和 `8 / (0)` 会报错。
- 取模表达式当前只接受两个 `int` 操作数，结果是 `int`；显式静态 `7 % 0` 和 `7 % (0)` 会报错。
- 除法赋值 `/=` 当前只接受已有 `int` 变量或参数作为目标，右侧值必须是 `int`；显式静态 `count /= 0` 和 `count /= (0)` 会报错。
- 取模赋值 `%=` 当前只接受已有 `int` 变量或参数作为目标，右侧值必须是 `int`；显式静态 `count %= 0` 和 `count %= (0)` 会报错。
- `< <= > >=` 只接受两个 `int`；`== !=` 接受同类型的 `int`、`bool` 或 `string`，结果都是 `bool`。字符串按内容比较，C 后端生成 `strcmp`。
- `not`、`and`、`or` 的 operand 和结果严格为 `bool`，不引入 truthiness；比较高于 `not`，`not` 高于 `and`，`and` 高于 `or`。
- `and` / `or` 运行时从左到右短路；C 后端为每层 AST 保留括号并生成 `!`、`&&`、`||`。
- `and`、`or`、`not` 是唯一源码形式，不支持 `&&`、`||`、`!` 符号别名。
- 当前不支持 bare `return`、void/main return、一般常量条件折叠、静态非空 `for` 证明、完整 CFG、不可达 warning 模式、倒序 `for`、负数步长、`for item in list`、带标签的 `break label` / `continue label`、`count++`、浮点数、动态整数范围分析、运行时错误恢复、动态非正 step 的恢复/反向循环语义、默认参数、命名参数、可变参数、函数重载、赋值表达式或单词关键字 `elseif`。
- 变量名和参数名使用 ASCII 字母、数字和 `_`，且不能以数字开头。
- 为保持旧示例兼容，`fn`、`main`、`let`、`print` 暂时仍可作为变量名或参数名；`if`、`else`、`return`、`while`、`for`、`from`、`to`、`step`、`through`、`break`、`continue`、`true`、`false`、`and`、`or`、`not` 不作为普通名字使用。

当前 v0.39 的完整默认 C 路径新增局部数组存储与边界检查，沿用严格 `bool`、单一 checked i32 和内部 `FlowOutcome` 控制流分析。`examples/local_arrays.ly` 的实际输出为 `95`、`LAI`、`1`。LLVM 不扩展数组能力：完整示例报 `FunctionDef`，纯 main 数组单测报 `LetStmt`。下一版为 v0.40 索引写入/只读长度/遍历，之后依次为 v0.41 多维数组、v0.42 反向循环、v0.43 字符串/最小用户标准库、v0.44 浮点数、v0.45 LLVM 变量模型与语义复盘；剩余 6 版，均未实现。数组参数/返回和整数组复制/赋值为未编号后续候选，不承诺版本。

新增用户可见语法前，先提供 2-3 个有意义的候选形式，并分别给出源码示例、利弊、与既有 LAI 语法的一致性、成熟语言实践和明确推荐；由用户选择最终语法。仅内部重构且不改变源码语法时，不制造虚假的语法选项。

## 编译器代码约定

- 保持 `compile_source(source: str, backend: Backend = C_BACKEND) -> str` 作为测试入口；省略后端时仍生成 C。
- 对用户可见的编译失败抛 `LaiCompileError`。
- 错误信息尽量包含 `line N`。
- 新增语法前先加测试。
- 不为 v0.x 提前引入外部 Python 依赖。
- 当前 `lai_compiler.py` 保留 lexer、parser、文件编译和 CLI，在解析/检查后默认委托完整 `C_BACKEND`；CLI 可用 `--backend {c,llvm}` 显式选择实验性 LLVM 后端。
- `lai_ast.py` 负责 AST 节点定义，新增语法节点优先放这里。
- `lai_types.py` 共享不可变 `ArrayType(element_type, length)` 与局部数组索引目标辅助，不引入完整类型系统。
- `lai_checker.py` 负责语义/类型检查。
- `lai_backend.py` 负责不可变的通用 `Backend` 描述符。
- `lai_clang.py` 负责共享 `clang` 调用和既有错误措辞。
- `lai_c_backend.py` 负责完整默认 C 源码生成和构建。
- `lai_llvm_backend.py` 负责不依赖 `llvmlite` 的受限文本 LLVM IR 发射，并复用共享 clang runner。
- `lai_stdlib.py` 只放内部标准库/运行时 C 输出辅助，不代表已经有用户可直接调用的标准库 API。

## 测试约定

核心测试命令：

```powershell
python -m unittest discover -v
```

端到端验证命令：

```powershell
python lai_compiler.py main.ly --run
python lai_compiler.py examples/basic_comparisons.ly --run
python lai_compiler.py examples/boolean_logic.ly --run
python lai_compiler.py examples/general_early_return.ly --run
python lai_compiler.py examples/local_arrays.ly --run
python lai_compiler.py examples/local_arrays.ly --backend llvm
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
python lai_compiler.py examples/llvm_arithmetic.ly --backend llvm --run
```

测试优先覆盖：

- 成功生成的关键 C 代码片段。
- 行号化错误。
- 符号表行为，例如未知变量和重复变量。
- 新语法的最小正例和反例。
- 数组同构类型、空数组、静态/动态边界、初始化顺序、索引单次求值、短路、作用域和 LLVM 能力拒绝；parser 接受节点形式不代表 checker 允许该语言能力。

2026-09-05 验证记录：完整 `python -m unittest discover -q` 和最终 `python -m unittest discover -v` 均为 449 项通过、无 skip，CLI help 的 v0.39 说明测试通过；全部既有 C/LLVM 示例成功，数组 LLVM 示例按预期 exit 1 并报第 1 行 `FunctionDef` 能力错误。详细输出见 `docs/ai/active-context.md`，不得把历史上传状态或测试总数当成本次证据。

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
- `examples/build/*.ll` 和 `examples/build/*.exe` 是 LLVM 示例生成的未跟踪输出，不应提交。
