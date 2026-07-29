import unittest

from lai_compiler import compile_source
from lai_core import LaiCompileError


class LaiFlowTests(unittest.TestCase):
    def test_accepts_guard_clause_with_fallback_return(self):
        generated = compile_source(
            """fn classify(value: int) -> int {
    if value < 0 {
        return -1
    }
    return 1
}

fn main() {
    print(classify(-2))
}"""
        )

        self.assertIn("return (-(1));", generated)
        self.assertIn("return 1;", generated)

    def test_accepts_multiple_guard_clauses(self):
        compile_source(
            """fn classify(value: int) -> int {
    if value < 0 {
        return -1
    }
    if value == 0 {
        return 0
    }
    return 1
}

fn main() {
}"""
        )

    def test_accepts_one_returning_branch_then_outer_fallback(self):
        compile_source(
            """fn choose(ready: bool) -> int {
    if ready {
        return 1
    } else {
        print(2)
    }
    return 3
}

fn main() {
}"""
        )

    def test_accepts_following_statement_when_one_branch_falls_through(self):
        generated = compile_source(
            """fn choose(ready: bool) -> int {
    if ready {
        return 1
    } else {
        print(2)
    }
    print(3)
    return 4
}

fn main() {
}"""
        )

        self.assertIn('printf("%d\\n", 3);', generated)

    def test_rejects_guard_clause_without_fallback_return(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_rejects_first_statement_after_direct_return_as_unreachable(self):
        source = """fn value() -> int {
    return 1
    print(missing)
    return "bad"
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 3: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_complete_returning_if_as_unreachable(self):
        source = """fn value(ready: bool) -> int {
    if ready {
        return 1
    } else {
        return 2
    }
    print(3)
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 7: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_complete_nested_return_as_unreachable(self):
        source = """fn value(first: bool, second: bool) -> int {
    if first {
        if second {
            return 1
        } else {
            return 2
        }
        print(missing)
    } else {
        return 3
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 8: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_break_in_returning_function(self):
        source = """fn value() -> int {
    while true {
        break
        print(missing)
    }
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 4: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_continue_in_returning_function(self):
        source = """fn value() -> int {
    while true {
        continue
        print(missing)
    }
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 4: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_break_in_void_function(self):
        source = """fn work() {
    while true {
        break
        print(missing)
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 4: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_continue_in_void_function(self):
        source = """fn work() {
    while true {
        continue
        print(missing)
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 4: unreachable statement$",
        ):
            compile_source(source)

    def test_preserves_wrong_return_type_diagnostic(self):
        source = """fn value() -> int {
    return "bad"
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 2: return type must be int, got string$",
        ):
            compile_source(source)

    def test_preserves_void_function_return_diagnostic(self):
        source = """fn work() {
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 2: return is only allowed in functions with return type$",
        ):
            compile_source(source)

    def test_preserves_main_return_diagnostic(self):
        source = """fn main() {
    return 1
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 2: return is only allowed in functions with return type$",
        ):
            compile_source(source)


if __name__ == "__main__":
    unittest.main()
