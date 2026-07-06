# LAI v0 Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable LAI compiler that translates a tiny English-keyword LAI program to C, compiles it with `clang`, and can run the result.

**Architecture:** Keep the compiler in one focused Python file for v0. The compiler parses a deliberately tiny line-oriented grammar, generates C, and shells out to `clang`; tests exercise the translation layer without requiring a full compiler run.

**Tech Stack:** Python 3.12, standard library `unittest`, LLVM/Clang already installed at `D:\Software\LLVM\bin`, MSVC Build Tools already installed.

## Global Constraints

- Source language uses English keywords in v0.
- Supported syntax is limited to `fn main()`, `let`, and `print`.
- Backend is C generation plus `clang`, not direct LLVM IR.
- Do not add external Python dependencies.
- Preserve `D:\Porject\TestProgrammingLanguage` as the project directory.

---

## File Structure

- `D:\Porject\TestProgrammingLanguage\main.lai`: sample LAI source program.
- `D:\Porject\TestProgrammingLanguage\lai_compiler.py`: v0 compiler CLI and translation logic.
- `D:\Porject\TestProgrammingLanguage\tests\test_lai_compiler.py`: unit tests for translation and validation.
- `D:\Porject\TestProgrammingLanguage\build\`: generated C and executable output.

### Task 1: Add Translation Tests

**Files:**
- Create: `D:\Porject\TestProgrammingLanguage\tests\test_lai_compiler.py`
- Modify: `D:\Porject\TestProgrammingLanguage\lai_compiler.py`

**Interfaces:**
- Consumes: none.
- Produces: `compile_source(source: str) -> str` and `LaiCompileError`.

- [ ] **Step 1: Write failing tests**

```python
import unittest

from lai_compiler import LaiCompileError, compile_source


class LaiCompilerTests(unittest.TestCase):
    def test_print_literal_and_variable(self):
        source = '''fn main() {
    print("Hello LAI")
    let name = "LingYu"
    print(name)
}'''

        c_code = compile_source(source)

        self.assertIn('#include <stdio.h>', c_code)
        self.assertIn('printf("Hello LAI\\n");', c_code)
        self.assertIn('const char* name = "LingYu";', c_code)
        self.assertIn('printf("%s\\n", name);', c_code)

    def test_rejects_unknown_variable(self):
        source = '''fn main() {
    print(name)
}'''

        with self.assertRaisesRegex(LaiCompileError, "unknown variable"):
            compile_source(source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_lai_compiler -v`
Expected: FAIL because `compile_source` and `LaiCompileError` are not implemented.

- [ ] **Step 3: Add minimal compiler implementation**

Replace `lai_compiler.py` with a compiler that exports:

```python
class LaiCompileError(Exception):
    pass


def compile_source(source: str) -> str:
    ...
```

The implementation validates the v0 grammar and emits C.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_lai_compiler -v`
Expected: PASS.

### Task 2: Add CLI, Sample Source, and Clang Build

**Files:**
- Create: `D:\Porject\TestProgrammingLanguage\main.lai`
- Modify: `D:\Porject\TestProgrammingLanguage\lai_compiler.py`

**Interfaces:**
- Consumes: `compile_source(source: str) -> str`.
- Produces: CLI command `python lai_compiler.py main.lai --run`.

- [ ] **Step 1: Create sample source**

```lai
fn main() {
    print("Hello LAI")
    let name = "LingYu"
    print(name)
}
```

- [ ] **Step 2: Add CLI behavior**

The CLI should:

- read the input `.lai` file;
- write generated C to `build/main.c`;
- run `clang build/main.c -o build/main.exe`;
- run the executable when `--run` is provided.

- [ ] **Step 3: Run end-to-end build**

Run: `python lai_compiler.py main.lai --run`
Expected output includes:

```text
Hello LAI
LingYu
```

### Task 3: Verify Existing Clang Path Works

**Files:**
- Modify: `D:\Porject\TestProgrammingLanguage\lai_compiler.py`

**Interfaces:**
- Consumes: CLI from Task 2.
- Produces: clearer error if `clang` cannot run from the active terminal.

- [ ] **Step 1: Add clang failure message**

If `clang` is missing or returns non-zero, print the command output and mention
using the `x64 Native Tools Command Prompt for VS`.

- [ ] **Step 2: Run verification**

Run: `python -m unittest tests.test_lai_compiler -v`
Expected: PASS.

Run: `python lai_compiler.py main.lai --run`
Expected: prints `Hello LAI` and `LingYu`.

## Self-Review

- Spec coverage: v0 grammar, C backend, compiler CLI, tests, and manual run are covered.
- Placeholder scan: no implementation placeholder is left for the task owner.
- Type consistency: `compile_source(source: str) -> str` and `LaiCompileError` are used consistently.
