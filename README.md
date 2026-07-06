# AIProgrammingLanguage

LAI / LingYu is an experimental programming language project.

The current version is a tiny v0 compiler loop:

```text
main.lai -> lai_compiler.py -> build/main.c -> clang -> build/main.exe
```

For v0, LAI uses a very small English-keyword syntax. The long-term direction is
not Chinese keywords, but a compact language surface, AI-friendly structure,
gradual typing, and a future LLVM backend.

## Current Syntax

```lai
fn main() {
    print("Hello LAI")
    let name = "JD"
    print(name)
}
```

v0 supports:

- `fn main() { ... }`
- `let name = "text"`
- `let count = 123`
- `print("text")`
- `print(name)`

v0 intentionally does not support user-defined functions, types, control flow,
GC, JIT, concurrency, or direct LLVM IR generation yet.

## Quick Start

Requirements:

- Python 3.12+
- Clang available in `Path`
- On Windows, Visual Studio Build Tools with MSVC and Windows SDK

Run the sample program:

```powershell
python lai_compiler.py main.lai --run
```

Expected output:

```text
Wrote build\main.c
Built build\main.exe
Hello LAI
JD
```

Run tests:

```powershell
python -m unittest tests.test_lai_compiler -v
```

## Project Layout

```text
lai_compiler.py   v0 compiler and CLI
main.lai          sample LAI source file
tests/            compiler translation tests
docs/             design notes and implementation plans
```

## Roadmap

- Expand the parser beyond the line-oriented v0 grammar.
- Add expressions, control flow, and user-defined functions.
- Introduce a gradual type system.
- Replace the temporary C backend with a real LLVM backend.
- Explore AI-native code structure and tooling.
