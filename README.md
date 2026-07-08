# AIProgrammingLanguage

LAI / 灵语是一个自研编程语言实验项目。

当前版本是 v0.9：语言能力还很小，但编译器内部已经整理成结构化管线：

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

fn main() {
    // LAI v0.9 demo
    print("Hello LAI")
    let name = "JD"
    print(name)
    greet()
    show_math()
    if 1 < 2 {
        print("math works")
    }
}
```

当前支持：

- `fn main() { ... }`
- `fn greet() { ... }`
- `// comment`
- `let name = "text"`
- `let count = 123`
- `let count = 1 + 2`
- `let ready = true`
- `let ok = count == 3`
- `print("text")`
- `print(123)`
- `print(1 + 2)`
- `print(true)`
- `print(1 < 2)`
- `print(name)`
- `if ready { ... }`
- `if 1 < 2 { ... }`
- `greet()`
- 正式源码扩展名：`.ly`
- 基础语义/类型检查：`string`、`int`、`bool`
- 标准库雏形：内部 `lai_stdlib.py` 管理 C preamble、字符串转义和 `print` 输出格式
- 编译器模块拆分：`lai_core.py`、`lai_checker.py`、`lai_c_backend.py`
- AST 节点拆分：`lai_ast.py`

当前暂不支持：

- 函数参数和返回值
- `else`
- 循环
- 类型标注或类型推断
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
Hello LAI
JD
Hello from function
3
count is three
math works
```

运行测试：

```powershell
python -m unittest discover -v
```

## 项目结构

```text
lai_compiler.py   v0.9 词法、语法、文件编译和命令行入口
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
- v0.10：补 `else` 或函数参数
- v0.11+：在 C 后端稳定后探索 LLVM 后端
