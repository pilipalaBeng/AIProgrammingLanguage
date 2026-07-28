import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from lai_compiler import compile_file


@unittest.skipUnless(shutil.which("clang"), "clang is required for LAI runtime tests")
class LaiRuntimeTests(unittest.TestCase):
    def compile_and_run(self, source: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_path = root / "program.ly"
            source_path.write_text(source, encoding="utf-8")
            _, executable_path = compile_file(source_path, root / "build")
            try:
                return subprocess.run(
                    [str(executable_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
            except subprocess.TimeoutExpired as exc:
                raise AssertionError("LAI runtime program timed out after 10 seconds") from exc

    def test_dynamic_integer_failures_are_deterministic(self):
        cases = [
            ("max_value() + 1", "integer addition overflow"),
            ("min_value() - 1", "integer subtraction overflow"),
            ("max_value() * 2", "integer multiplication overflow"),
            ("-min_value()", "integer unary negation overflow"),
            ("one() / zero()", "division by zero"),
            ("one() % zero()", "modulo by zero"),
            ("min_value() / negative_one()", "integer division overflow"),
            ("min_value() % negative_one()", "integer modulo overflow"),
        ]

        for expression, reason in cases:
            with self.subTest(expression=expression):
                result = self.compile_and_run(
                    "fn max_value() -> int {\n"
                    "    return 2147483647\n"
                    "}\n"
                    "fn min_value() -> int {\n"
                    "    return -2147483648\n"
                    "}\n"
                    "fn one() -> int {\n"
                    "    return 1\n"
                    "}\n"
                    "fn zero() -> int {\n"
                    "    return 0\n"
                    "}\n"
                    "fn negative_one() -> int {\n"
                    "    return -1\n"
                    "}\n"
                    "fn main() {\n"
                    f"    print({expression})\n"
                    "    print(999)\n"
                    "}"
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(
                    result.stderr, f"LAI runtime error: line 17: {reason}\n"
                )
                self.assertNotIn("999", result.stdout)

    def test_short_circuit_skips_dynamic_overflow_helpers(self):
        cases = [("false and max_value() + 1 > 0", "0\n"), ("true or max_value() + 1 > 0", "1\n")]

        for expression, expected_stdout in cases:
            with self.subTest(expression=expression):
                result = self.compile_and_run(
                    "fn max_value() -> int {\n"
                    "    return 2147483647\n"
                    "}\n"
                    "fn main() {\n"
                    f"    print({expression})\n"
                    "}"
                )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                self.assertEqual(result.stdout, expected_stdout)

    def test_dynamic_non_positive_step_fails_before_empty_range_body(self):
        for function_name, value in (("zero", "0"), ("negative", "-1")):
            with self.subTest(function_name=function_name):
                result = self.compile_and_run(
                    f"fn {function_name}() -> int {{\n"
                    f"    return {value}\n"
                    "}\n"
                    "fn main() {\n"
                    f"    for i from 1 to 0 step {function_name}() {{\n"
                    "        print(i)\n"
                    "    }\n"
                    "    print(999)\n"
                    "}"
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(
                    result.stderr,
                    "LAI runtime error: line 5: for step must be greater than 0\n",
                )
                self.assertNotIn("999", result.stdout)

    def test_dynamic_step_is_evaluated_once(self):
        result = self.compile_and_run(
            "fn step_value() -> int {\n"
            "    print(7)\n"
            "    return 2\n"
            "}\n"
            "fn main() {\n"
            "    for i from 0 through 4 step step_value() {\n"
            "        print(i)\n"
            "    }\n"
            "}"
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "7\n0\n2\n4\n")

    def test_for_continue_advances_and_break_skips_the_update(self):
        result = self.compile_and_run(
            "fn main() {\n"
            "    for i from 0 through 4 {\n"
            "        if i == 2 {\n"
            "            continue\n"
            "        }\n"
            "        print(i)\n"
            "    }\n"
            "    for j from 0 through 4 {\n"
            "        if j == 2 {\n"
            "            break\n"
            "        }\n"
            "        print(j)\n"
            "    }\n"
            "}"
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "0\n1\n3\n4\n0\n1\n")

    def test_through_i32_max_exits_without_overflow(self):
        result = self.compile_and_run(
            "fn main() {\n"
            "    for i from 2147483646 through 2147483647 {\n"
            "        print(i)\n"
            "    }\n"
            "}"
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "2147483646\n2147483647\n")
