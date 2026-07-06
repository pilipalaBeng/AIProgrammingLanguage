# LAI v0 Compiler Design

## Goal

Build the first usable LAI compiler loop:

```text
main.lai -> lai_compiler.py -> build/main.c -> clang -> build/main.exe
```

The first version uses English keywords. LAI's identity comes from a small,
AI-friendly language surface and a future high-performance backend, not from
Chinese keywords.

## Scope

LAI v0 supports only:

- `fn main() { ... }`
- `let name = "text"`
- `let count = 123`
- `print("text")`
- `print(name)`

LAI v0 does not support user-defined functions, conditionals, loops, types,
concurrency, GC, JIT, LLVM IR generation, or AI optimization.

## Syntax

Example source:

```lai
fn main() {
    print("Hello LAI")
    let name = "LingYu"
    print(name)
}
```

Rules:

- Blocks use `{}` in v0 because they are easier to parse reliably.
- Statements end by newline, not semicolon.
- Variable names may contain ASCII letters, digits, and `_`, and must not start
  with a digit.
- Strings use double quotes.
- Integers are decimal whole numbers.

## Compilation Strategy

`lai_compiler.py` reads a `.lai` file, validates the tiny v0 grammar, generates
C code, then invokes `clang`.

Generated C example:

```c
#include <stdio.h>

int main(void) {
    const char* name = "LingYu";
    printf("%s\n", name);
    return 0;
}
```

## Error Handling

The compiler should fail with line-numbered messages for unsupported syntax,
unknown variables, invalid variable names, and missing `fn main()`.

## Verification

The project should include a tiny sample `main.lai` and Python unit tests for
translation behavior. Manual end-to-end verification runs:

```powershell
python lai_compiler.py main.lai --run
```

Expected output:

```text
Hello LAI
LingYu
```
