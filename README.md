# AIProgrammingLanguage

LAI / 灵语是一个自研编程语言实验项目。

当前为 v0.40 第一阶段：在显式类型的固定长度局部数组上新增元素修改，长度 API 和遍历仍在 v0.40 待实现，不代表 v0.40 全量完成。完整默认路径仍是 C 后端；同时保留不依赖 `llvmlite` 的受限实验性文本 LLVM IR 后端。既有 guard clause、路径返回和不可达诊断继续有效；`int` 仍只有一种 checked i32 语义。

```text
main.ly -> lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang -> build/main.exe
```

LAI v0.x 暂时使用极简英文关键字语法。项目长期方向不是靠中文关键字做特色，而是探索更紧凑的语言表面、AI 友好的代码结构、渐进类型系统，以及未来的 LLVM 后端。

## 当前语法

v0.40 第一阶段元素修改示例（函数体内）：

```lai
let scores: int[] = [90, 95, 100]
scores[0] = 80
scores[0] += 5
print(scores[0])
```

输出 `85`。三种数组元素均允许同型 `=`；仅 `int` 元素支持 `+= -= *= /= %=`。先求值索引并检查边界，再读取旧值（仅复合赋值），再求值右值，各阶段单次执行，全部成功才写入；索引失败不执行右值，右值或算术失败不写入。checked i32、静态零除和静态/动态边界检查保留，数组长度不变。

完整示例 `examples/array_element_assignment.ly` 实际输出 `85`、`60`、`10`、`after`、`1`。

v0.39 局部数组示例：

```lai
fn show_arrays(index: int) {
    let scores: int[] = [90, 95, 100]
    let names: string[] = ["LAI", "LingYu"]
    let flags: bool[] = [true, scores[0] > 80]
    let empty: int[] = []
    print(scores[index])
    print(names[0])
    print(flags[1])
}

fn main() {
    show_arrays(1)
}
```

输出依次为 `95`、`LAI`、`1`；`bool` 沿用数字打印，`true` 打印为 `1`，`false` 打印为 `0`。仓库示例为 `examples/local_arrays.ly`，其中还展示了函数调用作为初始化元素。

既有标量和控制流语法示例：

```lai
fn greet() {
    print("Hello from function")
}

fn show_math() {
    let count = 1 + 2
    print(count)
    let ready = count == 3
    if ready {
        print("count is three")
    }
}

fn show_profile(name: string, count: int, ready: bool) {
    print(name)
    print(count)
    print(ready)
}

fn add(a: int, b: int) -> int {
    return a + b
}

fn label() -> string {
    return "Return label"
}

fn is_ready(count: int) -> bool {
    return count == 7
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
    print("Hello LAI")
    let name = "JD"
    print(name)
    greet()
    show_math()
    show_profile("Param JD", 7, true)
}

fn show_return_demo() {
    let total = add(3, 4)
    print(total)
    print(label())
    print(grade(85))
    print(first_over_two(5))
}

fn show_for_demo() {
  // for i from 0 to 3 {
  //     print(i)
  // }
  // for even from 0 to 6 step 2 {
  //     print(even)
  // }
  // for closed from 0 through 3 {
  //     print(closed)
  // }

    for j from 0 through 4 step 2{
        print(j)
    }
}

fn show_group_demo() {
    let grouped = (1 + 2)
    print(grouped)
    if (grouped == 3) {
        print("group works")
    }
}

fn show_subtract_demo() {
    let start = 5
    let result = start - 2
    result -= 1
    print(result)
}

fn show_multiply_demo() {
    let base = 2 + 3 * 4
    print(base)
    let grouped = (2 + 3) * 4
    grouped *= 2
    print(grouped)
}

fn show_division_demo() {
    let divided = 8 / 2
    print(divided)
    let grouped = (6 + 4) / 2
    print(grouped)
    let shrinking = 16
    shrinking /= 2
    print(shrinking)
}

fn show_modulo_demo() {
    let remainder = 7 % 3
    print(remainder)
    let grouped = (10 + 5) % 4
    print(grouped)
    let folded = 29
    folded %= 5
    print(folded)
}

fn show_while_demo() {
    let loop = 0
    while loop < 3 {
        print(loop)
        loop += 1
    }
}

fn show_loop_control_demo() {
    let control = 0
    while control < 5 {
        control += 1
        if control < 2 {
            continue
        }
        print(control)
        if control > 2 {
            break
        }
    }
}

fn show_return_bool_demo() {
    let total = add(3, 4)
    if is_ready(total) {
        print("return bool works")
    }
}

fn show_condition_demo() {
    if 1 < 2 {
        print("math works")
    }
    if false {
        print("unexpected")
    } else if true {
        print("else if works")
    } else {
        print("else fallback")
    }
}

fn main() {
    // LAI v0.38 demo
    // show_basic_demo()
    // show_return_demo()
    // show_while_demo()
    // show_loop_control_demo()
    // show_condition_demo()
     // show_return_bool_demo()
    // show_for_demo()
    show_group_demo()
    show_subtract_demo()
    show_multiply_demo()
    show_division_demo()
    show_modulo_demo()
}
```

当前支持：

- 必需显式局部数组声明 `let scores: int[] = [90, 95, 100]`；`int[]`、`string[]`、`bool[]` 同构且长度固定，支持有类型的 `[]`
- 数组初始化元素从左到右各求值一次；`scores[index]` 读取和修改使用从 0 开始的 `int` 索引，负数和 `index >= length` 均越界
- 三种数组元素支持同型 `=`，`int` 元素另支持 `+= -= *= /= %=`；修改是语句，不是赋值表达式
- 编译期可算出的越界直接报错；动态越界在访问内存前输出 `LAI runtime error: line N: array index out of bounds: index I, length L` 到 `stderr` 并以 `EXIT_FAILURE` 退出
- 索引标量可复用现有表达式、打印、函数标量实参和返回；声明作用域包括 main、用户函数、分支和循环
- `fn main() { ... }`
- `fn greet() { ... }`
- `fn show(name: string, count: int, ready: bool) { ... }`
- `fn add(a: int, b: int) -> int { ... }`
- `return a + b`
- `return a * b`
- `return a / b`
- `if score > 90 { return "A" } else if score > 80 { return "B" } else { return "C" }`
- 返回值函数可在条件、嵌套分支和循环路径中使用 `return expr`；guard clause 后的外层语句保持可达
- 所有可达路径必须精确返回；第一条不可达语句报 `line N: unreachable statement`
- `while true { return value }` 和任意括号包裹的 `(true)` 可作为保证返回路径；含 `break` 或发散路径时仍保守处理
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
- `count -= add(1, 2)`
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
- `for i from 0 to 3 { ... }`，其中 `to` 不包含终点，依次取 `0`、`1`、`2`
- `for i from 0 to 6 step 2 { ... }`
- `for i from 0 through 3 { ... }`，其中 `through` 包含终点，依次取 `0`、`1`、`2`、`3`
- `break`
- `continue`
- `greet()`
- `show("JD", 3, true)`
- 正式源码扩展名：`.ly`
- 基础语义/类型检查：`string`、`int`、`bool`
- 完整基础比较：`<`、`<=`、`>`、`>=` 只接受两个 `int`；`==`、`!=` 接受同类型的 `int`、`bool` 或 `string`
- 字符串 `==` / `!=` 按内容比较，C 后端生成 `strcmp(...) == 0` / `!= 0`
- 布尔逻辑源码关键字：`and`、`or`、`not`；三者是保留关键字，不支持 `&&`、`||`、`!` 源码别名
- `not`、`and`、`or` 只接受 `bool` operand 并返回 `bool`，不做整数或字符串 truthiness
- 表达式优先级为算术高于比较，比较高于 `not`，`not` 高于 `and`，`and` 高于 `or`；括号可覆盖分组
- `and` / `or` 运行时从左到右短路；C 后端生成保留 AST 括号的 `!`、`&&`、`||`
- 单一 checked i32 模式：纯静态零除和中间溢出在编译期拒绝；动态 `+ - *`、一元 `-`、`/`、`%` 和五种复合赋值通过 C 运行时助手检查
- 动态运行时失败写入 `stderr`，格式为 `LAI runtime error: line N: reason`，随后以 `EXIT_FAILURE` 终止
- `for` 的 start/end/step 按源码顺序各求值一次；动态 step 在进入循环前检查为正，范围感知推进使 `through 2147483647` 正常结束
- 每次 C 生成选择不与用户标识符冲突的内部前缀，运行时助手和循环临时变量不会撞名
- 标准库雏形：内部 `lai_stdlib.py` 管理 C preamble、字符串转义和 `print` 输出格式
- 编译器模块拆分：`lai_core.py`、`lai_checker.py`、`lai_backend.py`、`lai_c_backend.py`
- AST 节点拆分：`lai_ast.py`

当前暂不支持：

- `main` 返回类型
- bare `return`、无返回值函数或 `main` 中的 `return`
- 一般常量条件折叠，例如把 `not false`、比较结果或逻辑表达式证明为静态 `true`
- 静态非空 `for` 证明、完整 CFG 或 warning 模式的不可达代码处理
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++`
- 浮点数、动态整数范围分析、动态非正 `for step` 的恢复或反向循环语义
- 尚未设计的更多运算符层级
- 比较链，例如 `1 < 2 < 3`
- 字符串大小排序，例如 `"A" < "B"`
- 布尔逻辑符号别名 `&&`、`||`、`!`，以及非 `bool` 值的 truthiness
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 通用标量变量类型标注和完整类型推导；标量 `let` 沿用已有基础推导，局部显式标注只接受三种一维数组类型
- 隐式数组类型、数组参数/返回、整数组复制/赋值/比较/打印
- 长度 API、数组遍历、方法、切片和多维数组
- GC
- JIT
- 并发
- 完整 LLVM 后端：实验性 LLVM 路径只支持空 `main`，或顶层 `print` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；变量、赋值、比较、布尔、字符串、控制流和用户函数仍会报明确能力错误

## 快速开始

环境要求：

- Python 3.12+
- `clang` 已加入 `Path`
- Windows 下需要 Visual Studio Build Tools、MSVC 和 Windows SDK

运行示例程序：

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

`--backend {c,llvm}` 默认使用 `c`。v0.40 第一阶段在局部数组 C 存储和边界检查上增加元素修改，保留既有 checked i32 与控制流规则。实验性 LLVM 不扩展数组能力：纯 main 数组单测明确验证 `LetStmt` 能力错误；`examples/local_arrays.ly` 含用户函数，实际走 LLVM 时以 exit 1 报 `LAI compile error: line 1: LLVM backend does not support FunctionDef yet`。

`main.ly` 的预期输出：

```text
Wrote build\main.c
Built build\main.exe
3
group works
2
14
40
4
5
8
1
3
4
```

运行测试：

```powershell
python -m unittest discover -v
```

2026-09-05 验证结果：数组语义/真实 `clang` 运行测试 27 项通过，数组 AST/解析测试 23 项通过；完整回归 `python -m unittest discover -q` 和最终 `python -m unittest discover -v` 均为 449 项通过，无 skip。CLI help 显示 v0.39，对应测试已通过。`main.ly`、数组、比较、布尔逻辑、整数安全和早退 C 示例全部成功；一元整数示例 C/LLVM 输出一致，LLVM minimal/arithmetic 成功，数组 LLVM 拒绝行为符合上述边界。逐项输出见 `docs/ai/active-context.md` 的 v0.39 验证记录。发布提交与远端状态以 Git 记录及交付报告为准。

2026-09-07 v0.40 第一阶段验证：最终完整 `python -m unittest discover -q` 和 `python -m unittest discover -v` 均为 480 项通过、无 skip。CLI help v0.40 测试先失败后通过；新示例默认 C 与严格 C11 / `-O2` 输出一致，既有 C/LLVM 示例通过，新示例 LLVM 按预期以第 1 行 `FunctionDef` 能力错误退出。独立审查未发现真实缺陷、回归或阻塞缺口；详细证据见 `docs/ai/active-context.md`。

## 项目结构

```text
lai_compiler.py   v0.40 第一阶段词法、语法、后端无关的文件编译和命令行入口
lai_ast.py        AST 节点定义
lai_types.py      局部数组类型、长度与索引目标共享辅助
lai_int.py        i32 边界与纯整数字面量树静态求值辅助
lai_core.py       共享错误类型和核心规则
lai_checker.py    语义和基础类型检查
lai_backend.py    不可变的通用 Backend 描述符
lai_clang.py      共享 clang 调用和既有错误措辞
lai_c_backend.py  完整默认 C 源码生成和构建
lai_llvm_backend.py 实验性文本 LLVM IR 生成和构建
lai_stdlib.py     v0.7 标准库/运行时 C 输出辅助模块
main.ly           示例 LAI 源码
examples/basic_comparisons.ly C 后端基础比较可运行示例
examples/boolean_logic.ly C 后端布尔逻辑与短路可运行示例
examples/runtime_integer_safety.ly C 后端动态安全运算与 i32 上界范围示例
examples/general_early_return.ly C 后端通用早退与静态 true 循环示例
examples/local_arrays.ly C 后端局部数组创建和读取示例
examples/array_element_assignment.ly C 后端数组元素修改示例
tests/test_lai_flow.py 控制流结果、不可达诊断与所有路径返回测试
tests/test_lai_array_parser.py 数组 AST、声明和索引解析测试
tests/test_lai_arrays.py 数组语义、类型、静态边界与 LLVM 拒绝测试
tests/test_lai_array_runtime.py 数组真实 clang 运行测试
tests/test_lai_array_assignment.py 元素修改语义与 C 生成测试
tests/test_lai_array_assignment_runtime.py 元素修改真实 clang 运行测试
tests/            编译器翻译与解析测试
docs/             设计文档、实施计划和 AI 项目记忆
```

## 当前编译器结构

编译器已经按阶段拆分出多个入口：

- `lai_compiler.tokenize(source)`：词法分析，生成 token 列表
- `lai_compiler.parse_source(source)`：语法分析，生成 AST
- `lai_ast.py`：集中定义 `Program`、语句节点和表达式节点
- `lai_types.py`：共享不可变 `ArrayType(element_type, length)` 与局部数组索引目标辅助；`ArrayExpr`、`IndexExpr` 定义仍在 `lai_ast.py`
- `lai_checker.check_program(program)`：语义、基础类型和统一控制流检查；内部 `FlowOutcome` 不属于语言语法
- `lai_backend.py`：定义不可变的通用 `Backend` 描述符
- `lai_clang.py`：集中共享 `clang` 调用和既有错误措辞
- `lai_c_backend.C_BACKEND`：完整默认 C 后端，负责 C 生成和构建
- `lai_llvm_backend.LLVM_BACKEND`：实验性文本 LLVM IR 后端，不依赖 `llvmlite`
- `lai_c_backend.generate_c(program)`：把 AST 生成 C 代码
- `lai_stdlib.py`：集中管理完整 C preamble、checked i32 runtime、字符串转义和 `print` 的 C 输出格式
- 局部数组由 C 后端使用内部存储名声明，初始化元素逐条写入；空数组物理占位 1、逻辑长度 0，动态索引 helper 只求值索引一次且保留短路
- `IndexAssignStmt` 表示元素修改；C 后端按独立完整表达式保存已检查的元素地址、复合赋值旧值和右值，成功后写回
- `compile_source(source, backend=C_BACKEND)`：解析、检查后委托后端生成源码
- `compile_file(..., backend=C_BACKEND)`：读取 `.ly` 文件，委托后端写出生成物并构建
- `--backend {c,llvm}`：选择固定后端映射，省略时默认为 `c`

实验性 LLVM 后端仅支持空 `main` 或顶层 `print` 中的 `IntExpr`、`UnaryExpr`、`AddExpr`、`SubtractExpr`、`MultiplyExpr`、`DivideExpr`、`ModuloExpr`、`GroupExpr`；动态表达式、变量、赋值、`CompareExpr`、`LogicalNotExpr`、`LogicalExpr`、布尔、字符串、控制流和用户函数仍会报明确能力错误。基础比较和布尔逻辑的可运行 C 示例分别是 `examples/basic_comparisons.ly`、`examples/boolean_logic.ly`；LLVM 可运行示例是 `examples/unary_integer.ly`、`examples/llvm_minimal.ly` 和 `examples/llvm_arithmetic.ly`。共享 checker 在进入任一后端前拒绝纯静态零除和每个 i32 中间溢出，因此 LLVM 不再接受源码层静态回绕；安全的一元和算术示例仍可生成并运行。

## 路线图

完整版本规划见 `docs/ai/roadmap.md`。下一阶段建议小步推进：

- v0.9：已拆出 AST 节点模块
- v0.10：已支持最小 `else`
- v0.11：已支持 `else if`
- v0.12：已支持函数参数
- v0.13：已支持函数返回值和函数调用表达式
- v0.14：已支持分支 `return` 控制流
- v0.15：已支持最小 `while` 循环和变量重新赋值
- v0.16：已支持 `break` / `continue`
- v0.17：已支持循环体内局部 `return` 检查
- v0.18：已支持 `for i from 0 to 3`
- v0.19：已支持 `+=` 赋值语法糖
- v0.20：已支持 `for i from 0 to 6 step 2`
- v0.21：已支持包含终点循环，例如 `for i from 0 through 3`
- v0.22：已支持括号表达式，例如 `print((1 + 2))`
- v0.23：已支持普通减法，例如 `print(5 - 2)`
- v0.24：已支持 `-=` 减法赋值语法糖
- v0.25：已支持普通乘法，例如 `print(2 * 3)`
- v0.26：已支持 `*=` 乘法赋值语法糖
- v0.27：已支持普通除法，例如 `print(8 / 2)`
- v0.28：已支持 `/=` 除法赋值语法糖
- v0.29：已支持普通取模，例如 `print(7 % 3)`
- v0.30：已支持 `%=` 取模赋值语法糖
- v0.31：已建立通用后端描述符与 C 后端边界，默认行为仍为 C
- v0.32：已提供不依赖 `llvmlite` 的实验性文本 LLVM IR 后端和 `--backend {c,llvm}`
- v0.33：已完成 LLVM 整数算术表达式 lowering，并提供 `examples/llvm_arithmetic.ly`
- v0.34：已完成前缀一元整数表达式、i32 静态边界和 C/LLVM 可运行示例
- v0.35：已完成六种基础比较、类型矩阵、字符串内容比较和 C 可运行示例
- v0.36：已支持严格 `bool` 的 `and` / `or` / `not`、从左到右短路和 C lowering；LLVM 仍不支持两个逻辑 AST
- v0.37：已完成单一 checked i32 模式、纯静态编译期诊断、动态 C 运行时检查及范围感知 `for` 推进
- v0.38：已完成通用函数早退、不可达诊断、精确所有路径返回和最小静态 `while true` 证明
- v0.39：已完成显式类型固定长度局部数组、只读索引、类型和边界检查；历史验证状态见上文
- v0.40 第一阶段：元素修改已实现；下一步仍在 v0.40 补只读长度和遍历
- 后续：v0.41 多维数组、v0.42 反向循环、v0.43 字符串/最小用户标准库、v0.44 浮点数、v0.45 LLVM 变量模型与语义复盘，均未实现
- 尚有工作的编号队列为 v0.40-v0.45，共 6 个版本；完整边界见 `docs/ai/roadmap.md`
- 数组参数/返回、整数组复制/赋值已明确登记为未编号后续候选，生命周期和复制语义待设计，不承诺具体版本；多维数组基于数组核心继续推进
