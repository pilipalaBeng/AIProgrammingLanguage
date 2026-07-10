# AIProgrammingLanguage

LAI / 灵语是一个自研编程语言实验项目。

当前版本是 v0.25：语言能力还很小，但编译器内部已经整理成结构化管线：

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
    print(grouped)
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
    // LAI v0.25 demo
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
}
```

当前支持：

- `fn main() { ... }`
- `fn greet() { ... }`
- `fn show(name: string, count: int, ready: bool) { ... }`
- `fn add(a: int, b: int) -> int { ... }`
- `return a + b`
- `return a * b`
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
- `let count = add(1, 2)`
- `count = count + 1`
- `count += 1`
- `count -= 1`
- `count -= add(1, 2)`
- `let ready = true`
- `let ok = count == 3`
- `print("text")`
- `print(123)`
- `print(1 + 2)`
- `print((1 + 2))`
- `print(5 - 2)`
- `print(2 * 3)`
- `print(2 + 3 * 4)`
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
- 编译器模块拆分：`lai_core.py`、`lai_checker.py`、`lai_c_backend.py`
- AST 节点拆分：`lai_ast.py`

当前暂不支持：

- `main` 返回类型
- 通用 `return` 早退，例如循环外的非最终 `if { return ... }`
- `while true { return ... }` 作为保证返回路径
- `for` 的倒序循环、负数步长和 `for item in list`
- 带标签的 `break label` / `continue label`
- 自增语法 `count++` 和 `*=`, `/=` 等其他复合赋值
- 除法、负数和完整运算符优先级
- 默认参数、命名参数、可变参数和函数重载
- 单词关键字 `elseif`
- 变量类型标注或类型推断
- GC
- JIT
- 并发
- 直接生成 LLVM IR

## 快速开始

环境要求：

- Python 3.12+
- `clang` 已加入 `Path`
- Windows 下需要 Visual Studio Build Tools、MSVC 和 Windows SDK

运行示例程序：

```powershell
python lai_compiler.py main.ly --run
```

预期输出：

```text
Wrote build\main.c
Built build\main.exe
3
group works
2
14
20
```

运行测试：

```powershell
python -m unittest discover -v
```

## 项目结构

```text
lai_compiler.py   v0.25 词法、语法、文件编译和命令行入口
lai_ast.py        AST 节点定义
lai_core.py       共享错误类型和核心规则
lai_checker.py    语义和基础类型检查
lai_c_backend.py  C 后端代码生成
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
- `lai_c_backend.generate_c(program)`：把 AST 生成 C 代码
- `lai_stdlib.py`：集中管理 C preamble、字符串转义和 `print` 的 C 输出格式
- `compile_source(source)`：对外的源码编译入口
- `compile_file(...)`：读取 `.ly` 文件、生成 C、调用 `clang`

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
- v0.26：建议设计 `*=` 乘法赋值语法糖
- v0.27+：在 C 后端稳定后探索 LLVM 后端
