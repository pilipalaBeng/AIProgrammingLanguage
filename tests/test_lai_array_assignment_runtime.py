import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from lai_compiler import compile_file


TRACE = 'fn trace(n: int) -> int {\nprint(n)\nreturn n\n}\n'


@unittest.skipUnless(shutil.which("clang"), "clang is required for LAI array assignment runtime tests")
class LaiArrayAssignmentRuntimeTests(unittest.TestCase):
    def run_source(self, source, optimize=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "array_assignment.ly"
            path.write_text(source, encoding="utf-8")
            generated, executable = compile_file(path, root / "build")
            if optimize:
                executable = root / "optimized.exe"
                build = subprocess.run(
                    ["clang", "-O2", str(generated), "-o", str(executable)],
                    capture_output=True, text=True, timeout=30, check=False,
                )
                self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            return subprocess.run(
                [str(executable)], capture_output=True, text=True,
                timeout=10, check=False,
            )

    def assert_success(self, source, expected, optimize=False):
        result = self.run_source(source, optimize=optimize)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, expected)

    def assert_runtime_error(self, source, line, message, stdout="", optimize=False):
        result = self.run_source(source, optimize=optimize)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, stdout)
        self.assertEqual(result.stderr, f"LAI runtime error: line {line}: {message}\n")

    def test_all_integer_assignment_operators_update_only_selected_element(self):
        self.assert_success(
            'fn main() {\nlet scores: int[] = [90, 95, 100]\nlet i = 1\n'
            'scores[i] = 80\nprint(scores[i])\n'
            'scores[i] += 5\nprint(scores[i])\n'
            'scores[i] -= 1\nprint(scores[i])\n'
            'scores[i] *= 2\nprint(scores[i])\n'
            'scores[i] /= 2\nprint(scores[i])\n'
            'scores[i] %= 10\nprint(scores[i])\n'
            'print(scores[0])\nprint(scores[2])\n}',
            "80\n85\n84\n168\n84\n4\n90\n100\n",
        )

    def test_plain_assignment_all_types_and_string_replacement(self):
        self.assert_success(
            'fn replacement() -> string {\nprint(10)\nreturn "100% LAI"\n}\n'
            'fn main() {\nlet numbers: int[] = [1]\n'
            'let names: string[] = ["before", "untouched"]\n'
            'let flags: bool[] = [false]\nlet i = 0\n'
            'let original = names[i]\nnumbers[i] = -2147483648\n'
            'names[i] = replacement()\nflags[i] = names[i] == "100% LAI"\n'
            'print(numbers[i])\nprint(names[i])\nprint(names[1])\n'
            'print(original)\nprint(flags[i])\n}',
            "10\n-2147483648\n100% LAI\nuntouched\nbefore\n1\n",
        )

    def test_boolean_assignment_preserves_rhs_short_circuit(self):
        self.assert_success(
            TRACE + 'fn flag(n: int) -> bool {\nprint(n)\nreturn true\n}\n'
            'fn main() {\nlet flags: bool[] = [true]\n'
            'let empty: bool[] = []\nlet bad = 0\n'
            'flags[trace(0)] = false and empty[bad]\nprint(flags[0])\n'
            'flags[trace(0)] = true or flag(999)\nprint(flags[0])\n'
            'flags[trace(0)] = flags[0] and flag(7)\nprint(flags[0])\n}',
            "0\n0\n0\n1\n0\n7\n1\n",
        )

    def test_index_then_rhs_run_once_for_every_operator(self):
        for operator, expected in (("=", 3), ("+=", 23), ("-=", 17),
                                   ("*=", 60), ("/=", 6), ("%=", 2)):
            with self.subTest(operator=operator):
                self.assert_success(
                    TRACE + 'fn main() {\nlet scores: int[] = [20, 99]\n'
                    f'scores[trace(0)] {operator} trace(3)\n'
                    'print(scores[0])\nprint(scores[1])\n}',
                    f"0\n3\n{expected}\n99\n",
                )

    def test_updates_in_function_branch_while_and_for_scopes(self):
        self.assert_success(
            'fn update(n: int) -> int {\nlet scores: int[] = [0, 10]\n'
            'while scores[0] < n {\nscores[0] += 1\n}\n'
            'if scores[0] == n {\nlet local: int[] = [2]\n'
            'local[0] *= 3\nscores[1] = local[0]\n}\n'
            'for i from 0 to 3 {\nlet local: int[] = [i]\n'
            'local[0] += 1\nscores[1] += local[0]\n}\n'
            'return scores[0] + scores[1]\n}\n'
            'fn main() {\nprint(update(3))\nprint(update(1))\n}',
            "15\n13\n",
        )

    def test_parenthesized_target_and_same_slot_rhs_use_previous_value(self):
        self.assert_success(
            TRACE + 'fn main() {\nlet scores: int[] = [5]\n'
            '(scores)[trace(0)] = scores[trace(0)] + 1\nprint(scores[0])\n'
            '((scores))[trace(0)] += scores[trace(0)]\nprint(scores[0])\n'
            '(scores)[trace(0)] *= scores[trace(0)]\nprint(scores[0])\n}',
            "0\n0\n6\n0\n0\n12\n0\n0\n144\n",
        )

    def test_nested_dynamic_indices_succeed_in_order(self):
        self.assert_success(
            TRACE + 'fn main() {\nlet scores: int[] = [10, 20, 30]\n'
            'let indices: int[] = [2, 0]\n'
            'scores[indices[trace(0)]] += trace(7)\n'
            'scores[indices[trace(1)]] = scores[indices[trace(0)]]\n'
            'print(scores[0])\nprint(scores[1])\nprint(scores[2])\n}',
            "0\n7\n1\n0\n37\n20\n37\n",
        )

    def test_nested_dynamic_index_failures_prevent_rhs(self):
        for index, error in ((1, "index 3, length 3"), (2, "index 2, length 2")):
            with self.subTest(index=index):
                self.assert_runtime_error(
                    TRACE + 'fn main() {\nlet scores: int[] = [10, 20, 30]\n'
                    'let indices: int[] = [2, 3]\n'
                    f'scores[indices[trace({index})]] += trace(999)\nprint(888)\n}}',
                    8, f"array index out of bounds: {error}", f"{index}\n",
                )

    def test_plain_assignment_dynamic_bounds_for_all_element_types(self):
        for kind, value in (("int", "42"), ("string", '"LAI"'), ("bool", "true")):
            for literal, length, index in ((f"[{value}]", 1, -1),
                                           (f"[{value}]", 1, 1), ("[]", 0, 0)):
                with self.subTest(kind=kind, index=index, length=length):
                    self.assert_runtime_error(
                        f'fn rhs() -> {kind} {{\nprint(999)\nreturn {value}\n}}\n'
                        f'fn main() {{\nlet scores: {kind}[] = {literal}\n'
                        f'let i = {index}\nscores[i] = rhs()\nprint(888)\n}}',
                        8, f"array index out of bounds: index {index}, length {length}",
                    )

    def test_compound_assignment_checks_bounds_before_rhs(self):
        for operator in ("+=", "-=", "*=", "/=", "%="):
            for literal, index, length in (("[42]", -1, 1), ("[42]", 1, 1), ("[]", 0, 0)):
                with self.subTest(operator=operator, index=index, length=length):
                    self.assert_runtime_error(
                        TRACE + f'fn main() {{\nlet scores: int[] = {literal}\n'
                        f'scores[trace({index})] {operator} trace(999)\nprint(888)\n}}',
                        7, f"array index out of bounds: index {index}, length {length}",
                        f"{index}\n",
                    )

    def test_compound_overflow_reports_assignment_line_after_rhs(self):
        for operator, initial, rhs, operation in (
            ("+=", 2147483647, 1, "addition"),
            ("-=", -2147483648, 1, "subtraction"),
            ("*=", 2147483647, 2, "multiplication"),
            ("/=", -2147483648, -1, "division"),
            ("%=", -2147483648, -1, "modulo"),
        ):
            with self.subTest(operator=operator):
                self.assert_runtime_error(
                    TRACE + f'fn main() {{\nlet scores: int[] = [{initial}]\n'
                    f'scores[trace(0)] {operator} trace({rhs})\nprint(scores[0])\n}}',
                    7, f"integer {operation} overflow", f"0\n{rhs}\n",
                )

    def test_dynamic_division_and_modulo_by_zero_report_assignment_line(self):
        for operator, message in (("/=", "division by zero"), ("%=", "modulo by zero")):
            with self.subTest(operator=operator):
                self.assert_runtime_error(
                    TRACE + 'fn main() {\nlet scores: int[] = [42]\nlet zero = 0\n'
                    f'scores[trace(0)] {operator} trace(zero)\nprint(scores[0])\n}}',
                    8, message, "0\n0\n",
                )

    def test_index_arithmetic_failure_precedes_rhs_and_bounds(self):
        for index, value, message in (("i + 1", 2147483647, "integer addition overflow"),
                                      ("1 / i", 0, "division by zero")):
            with self.subTest(index=index):
                self.assert_runtime_error(
                    TRACE + 'fn main() {\nlet scores: int[] = []\n'
                    f'let i = {value}\nscores[{index}] = trace(999)\nprint(888)\n}}',
                    8, message,
                )

    def test_rhs_failure_reports_rhs_line_and_stops_execution(self):
        for operator in ("=", "+="):
            with self.subTest(operator=operator):
                self.assert_runtime_error(
                    TRACE + 'fn rhs() -> int {\nlet empty: int[] = []\n'
                    'return empty[trace(1)]\n}\n'
                    'fn main() {\nlet scores: int[] = [10]\n'
                    f'scores[trace(0)] {operator} rhs()\nprint(scores[0])\n}}',
                    7, "array index out of bounds: index 1, length 0", "0\n1\n",
                )

    def test_internal_prefixes_and_array_named_like_function_do_not_collide(self):
        self.assert_success(
            'fn scores() -> int {\nreturn 7\n}\n'
            'fn main() {\nlet __lai_internal_array_index = 0\n'
            'let __lai_internal__array_storage_1: string[] = ["before"]\n'
            'let __lai_internal__array_slot_2 = 2\n'
            'let __lai_internal__array_old_value_3 = 3\n'
            'let __lai_internal__array_value_4 = 4\n'
            'let scores: int[] = [scores()]\n'
            'scores[__lai_internal_array_index] += scores()\n'
            '__lai_internal__array_storage_1[0] = "after"\n'
            'print(scores[0])\nprint(scores())\n'
            'print(__lai_internal__array_storage_1[0])\n'
            'print(__lai_internal__array_slot_2)\n'
            'print(__lai_internal__array_old_value_3)\n'
            'print(__lai_internal__array_value_4)\n}',
            "14\n7\nafter\n2\n3\n4\n",
        )

    def test_optimized_execution_preserves_order_bounds_and_checked_arithmetic(self):
        self.assert_success(
            TRACE + 'fn main() {\nlet scores: int[] = [20]\n'
            'scores[trace(0)] += trace(3)\n'
            'scores[trace(0)] *= scores[trace(0)]\nprint(scores[0])\n}',
            "0\n3\n0\n0\n529\n", optimize=True,
        )
        for initial, index, operator, rhs, message, stdout in (
            (42, 1, "=", 999, "array index out of bounds: index 1, length 1", "1\n"),
            (2147483647, 0, "+=", 1, "integer addition overflow", "0\n1\n"),
            (-2147483648, 0, "/=", -1, "integer division overflow", "0\n-1\n"),
            (42, 0, "%=", 0, "modulo by zero", "0\n0\n"),
        ):
            with self.subTest(operator=operator, message=message):
                self.assert_runtime_error(
                    TRACE + f'fn main() {{\nlet scores: int[] = [{initial}]\n'
                    f'scores[trace({index})] {operator} trace({rhs})\nprint(scores[0])\n}}',
                    7, message, stdout, optimize=True,
                )


if __name__ == "__main__":
    unittest.main()
