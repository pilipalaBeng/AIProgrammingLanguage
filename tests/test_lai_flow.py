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

    def test_accepts_static_true_loop_as_only_returning_statement(self):
        generated = compile_source(
            """fn value() -> int {
    while true {
        return 1
    }
}

fn main() {
    print(value())
}"""
        )

        self.assertIn("while (1) {", generated)
        self.assertIn("return 1;", generated)

    def test_accepts_grouped_static_true_loop(self):
        compile_source(
            """fn value() -> int {
    while (true) {
        return 1
    }
}

fn main() {
}"""
        )

    def test_accepts_nested_grouped_static_true_loop(self):
        compile_source(
            """fn value() -> int {
    while ((true)) {
        return 1
    }
}

fn main() {
}"""
        )

    def test_accepts_complete_returning_if_inside_static_true_loop(self):
        compile_source(
            """fn value(ready: bool) -> int {
    while true {
        if ready {
            return 1
        } else {
            return 2
        }
    }
}

fn main() {
}"""
        )

    def test_accepts_guard_clause_and_fallback_inside_static_true_loop(self):
        compile_source(
            """fn value(ready: bool) -> int {
    while true {
        if ready {
            return 1
        }
        return 2
    }
}

fn main() {
}"""
        )

    def test_rejects_ordinary_while_as_guaranteed_return(self):
        source = """fn value(ready: bool) -> int {
    while ready {
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

    def test_rejects_static_true_loop_with_return_and_diverge_paths(self):
        source = """fn value(ready: bool) -> int {
    while true {
        if ready {
            return 1
        }
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_rejects_static_true_continue_loop_as_return(self):
        source = """fn value() -> int {
    while true {
        continue
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_rejects_static_true_loop_with_current_break_path(self):
        source = """fn value(ready: bool) -> int {
    while true {
        if ready {
            break
        }
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

    def test_accepts_fallback_return_after_static_true_loop_break_path(self):
        compile_source(
            """fn value(ready: bool) -> int {
    while true {
        if ready {
            break
        }
        return 1
    }
    return 2
}

fn main() {
}"""
        )

    def test_rejects_not_false_as_static_true_proof(self):
        source = """fn value() -> int {
    while not false {
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

    def test_rejects_static_non_empty_for_as_guaranteed_return(self):
        source = """fn value() -> int {
    for i from 0 through 0 {
        return i
    }
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_inner_loop_break_does_not_break_static_outer_loop(self):
        compile_source(
            """fn value() -> int {
    while true {
        while true {
            break
        }
        return 1
    }
}

fn main() {
}"""
        )

    def test_outer_break_path_still_prevents_guaranteed_return(self):
        source = """fn value(ready: bool) -> int {
    while true {
        while true {
            break
        }
        if ready {
            break
        }
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

    def test_ordinary_while_preserves_inner_diverge_path(self):
        source = """fn value(ready: bool) -> int {
    while ready {
        while true {
            continue
        }
    }
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_for_preserves_inner_diverge_path(self):
        source = """fn value() -> int {
    for i from 0 to 1 {
        while true {
            continue
        }
    }
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 1: function value must end with return$",
        ):
            compile_source(source)

    def test_rejects_statement_after_static_loop_with_return_and_diverge(self):
        source = """fn value(ready: bool) -> int {
    while true {
        if ready {
            return 1
        }
    }
    return 2
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 7: unreachable statement$",
        ):
            compile_source(source)

    def test_rejects_statement_after_static_diverging_loop(self):
        source = """fn value() -> int {
    while true {
        continue
    }
    return 1
}

fn main() {
}"""

        with self.assertRaisesRegex(
            LaiCompileError,
            r"^line 5: unreachable statement$",
        ):
            compile_source(source)

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
