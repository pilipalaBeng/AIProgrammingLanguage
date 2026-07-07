# AIProgrammingLanguage

LAI / 灵语是一个自研编程语言实验项目。

当前版本是 v0.4：语言能力还很小，但编译器内部已经整理成结构化管线：

```text
main.lai -> lexer -> parser -> AST -> C codegen -> clang -> build/main.exe
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
    // LAI v0.4 demo
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
python lai_compiler.py main.lai --run
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
python -m unittest tests.test_lai_compiler -v
```

## 项目结构

```text
lai_compiler.py   v0.4 编译器和命令行入口
main.lai          示例 LAI 源码
tests/            编译器翻译与解析测试
docs/             设计文档、实施计划和 AI 项目记忆
```

## 当前编译器结构

`lai_compiler.py` 内部已经按编译器阶段拆分：

- `tokenize(source)`：词法分析，生成 token 列表
- `parse_source(source)`：语法分析，生成 AST
- `generate_c(program)`：把 AST 生成 C 代码
- `compile_source(source)`：对外的源码编译入口
- `compile_file(...)`：读取 `.lai` 文件、生成 C、调用 `clang`

## 路线图

完整版本规划见 `docs/ai/roadmap.md`。下一阶段建议小步推进：

- v0.4：已支持零参数用户函数和函数调用语句
- v0.5：基础类型检查和更清楚的错误提示
- v0.6：文件拆分和小型标准库雏形
- v0.7+：在 C 后端稳定后探索 LLVM 后端
