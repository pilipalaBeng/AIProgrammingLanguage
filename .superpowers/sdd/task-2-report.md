# LAI v0.31 Task 2 Report: Backend Compiler Dispatch

## Status

Completed. Compiler orchestration now accepts an injected `Backend`, validates
the parsed program before emission, and delegates artifact naming and building
through that backend.

## Scope

Modified implementation and tests:

- `lai_compiler.py`
- `tests/test_lai_backend.py`
- `tests/test_lai_module_boundaries.py`
- `tests/test_lai_compiler.py`

No Task 3 documentation synchronization was performed.

## TDD Evidence

### RED

Command:

```powershell
python -m unittest tests.test_lai_backend.LaiBackendTests.test_compile_source_can_emit_with_an_injected_backend tests.test_lai_backend.LaiBackendTests.test_compile_source_checks_before_backend_emission tests.test_lai_backend.LaiBackendTests.test_compile_file_uses_backend_suffix_emitter_and_builder -v
```

Key output:

```text
ERROR: test_compile_source_can_emit_with_an_injected_backend
TypeError: compile_source() takes 1 positional argument but 2 were given

ERROR: test_compile_source_checks_before_backend_emission
TypeError: compile_source() takes 1 positional argument but 2 were given

ERROR: test_compile_file_uses_backend_suffix_emitter_and_builder
TypeError: compile_file() takes 2 positional arguments but 3 were given

Ran 3 tests in 0.003s
FAILED (errors=3)
```

### GREEN

Command:

```powershell
python -m unittest tests.test_lai_backend tests.test_lai_module_boundaries tests.test_lai_compiler.LaiCompilerTests.test_cli_help_uses_ly_source_extension -v
```

Key output:

```text
Ran 13 tests in 0.005s
OK
```

## Full Verification

Command:

```powershell
python -m unittest discover -v
```

Key output:

```text
Ran 244 tests in 0.023s
OK
```

## Commit

`e87b2843f7983d6acc10995d60d503f2342b89ff Route compiler through backend`

## Self-Review

- `compile_source` parses, calls `check_program`, then calls `backend.emit`.
- Invalid programs do not reach an injected emitter; this is directly covered
  by `test_compile_source_checks_before_backend_emission`.
- `compile_file` uses `backend.source_suffix`, writes its emitted artifact, and
  calls `backend.build(artifact_path, exe_path)`.
- Default behavior remains C-backed through `C_BACKEND`; the boundary test
  verifies compiler re-exports of `Backend`, `C_BACKEND`, and `generate_c`.
- `_run_clang` is removed from the compiler orchestration. `subprocess` remains
  only for the CLI `--run` executable launch.
- `git diff --check` and `git diff --cached --check` completed without errors.
- No unrelated source or Task 3 documentation files were changed.
