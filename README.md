# AIProgrammingLanguage

LAI / 灵语是一个自研编程语言实验项目。

当前版本是 v0.32：语言能力仍然很小，完整默认路径仍是 C 后端；同时提供一个不依赖 `llvmlite` 的实验性文本 LLVM IR 后端。

```text
main.ly -> lexer -> parser -> AST -> semantic/type checker -> C codegen + stdlib helpers -> clang -> build/main.exe
```

LAI v0.x 暂时使用极简英文关键字语法。项目长期方向不是靠中文关键字做特色，而是探索更紧凑的语言表面、AI 友好的代码结构、渐进类型系统，以及未来的 LLVM 后端。

## 当前语法

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
    // LAI v0.32 demo
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

- `fn main() { ... }`
- `fn greet() { ... }`
- `fn show(name: string, count: int, ready: bool) { ... }`
- `fn add(a: int, b: int) -> int { ... }`
- `return a + b`
- `return a * b`
- `return a / b`
- `if score > 90 { return "A" } else if score > 80 { return "B" } else { return "C" }`
- 返回值函数可在 `while` / `for` 循环体内提前 `return`，但函数末尾仍需要兜底 `return`
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
- 标准库雏形：内部 `lai_stdlib.py` 管理 C preamble、字符串转义和 `print` 输出格式
- 编译器模块拆分：`lai_core.py`、`lai_checker.py`、`lai_backend.py`、`lai_c_backend.py`
- AST 节点拆分：`lai_ast.py`

当前暂不支持：

- `main` 返回类型
- 通用 `return` 早退，例如循环外的非最终 `if { return ... }`
- `while true { return ... }` 作为保证返回路径
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++`
- 浮点数、负数、动态运行时除零检查和完整运算符优先级
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 变量类型标注或类型推断
- GC
- JIT
- 并发
- 完整 LLVM 后端：实验性 LLVM 路径只接受空 `main`，或 `print(0..2147483647)` 整数字面量；其他有效 LAI 程序会报明确的 LLVM 能力错误

## 快速开始

环境要求：

- Python 3.12+
- `clang` 已加入 `Path`
- Windows 下需要 Visual Studio Build Tools、MSVC 和 Windows SDK

运行示例程序：

```powershell
python lai_compiler.py main.ly --run
```

运行实验性 LLVM 示例：

```powershell
python lai_compiler.py examples/llvm_minimal.ly --backend llvm --run
```

`--backend {c,llvm}` 默认使用 `c`。C 后端保持完整；LLVM 后端只生成文本 IR，
不使用 `llvmlite`，且 v0.32 没有新增 LAI 源码语法。

预期输出：

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

## 项目结构

```text
lai_compiler.py   v0.32 词法、语法、后端无关的文件编译和命令行入口
lai_ast.py        AST 节点定义
lai_core.py       共享错误类型和核心规则
lai_checker.py    语义和基础类型检查
lai_backend.py    不可变的通用 Backend 描述符
lai_clang.py      共享 clang 调用和既有错误措辞
lai_c_backend.py  完整默认 C 源码生成和构建
lai_llvm_backend.py 实验性文本 LLVM IR 生成和构建
lai_stdlib.py     v0.7 标准库/运行时 C 输出辅助模块
main.ly           示例 LAI 源码
tests/            编译器翻译与解析测试
docs/             设计文档、实施计划和 AI 项目记忆
```

## 当前编译器结构

编译器已经按阶段拆分出多个入口：

- `lai_compiler.tokenize(source)`：词法分析，生成 token 列表
- `lai_compiler.parse_source(source)`：语法分析，生成 AST
- `lai_ast.py`：集中定义 `Program`、语句节点和表达式节点
- `lai_checker.check_program(program)`：语义和基础类型检查
- `lai_backend.py`：定义不可变的通用 `Backend` 描述符
- `lai_clang.py`：集中共享 `clang` 调用和既有错误措辞
- `lai_c_backend.C_BACKEND`：完整默认 C 后端，负责 C 生成和构建
- `lai_llvm_backend.LLVM_BACKEND`：实验性文本 LLVM IR 后端，不依赖 `llvmlite`
- `lai_c_backend.generate_c(program)`：把 AST 生成 C 代码
- `lai_stdlib.py`：集中管理 C preamble、字符串转义和 `print` 的 C 输出格式
- `compile_source(source, backend=C_BACKEND)`：解析、检查后委托后端生成源码
- `compile_file(..., backend=C_BACKEND)`：读取 `.ly` 文件，委托后端写出生成物并构建
- `--backend {c,llvm}`：选择固定后端映射，省略时默认为 `c`

实验性 LLVM 后端仅支持空 `main` 或 `print(0..2147483647)` 整数字面量；范围外但语义有效的 LAI 程序会报明确能力错误。可运行示例是 `examples/llvm_minimal.ly`。下一步推荐先完成整数算术表达式 lowering，再考虑变量/SSA 或控制流。

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
- v0.32：已提供不依赖 `llvmlite` 的实验性文本 LLVM IR 后端和 `--backend {c,llvm}`；下一步推荐整数算术表达式 lowering，先于变量/SSA 或控制流
