import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from lai_compiler import compile_file


@unittest.skipUnless(shutil.which("clang"), "clang is required for LAI array runtime tests")
class LaiArrayRuntimeTests(unittest.TestCase):
    def run_source(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "arrays.ly"
            path.write_text(source, encoding="utf-8")
            _, executable = compile_file(path, root / "build")
            return subprocess.run([str(executable)], capture_output=True, text=True,
                                  timeout=10, check=False)

    def assert_success(self, source, expected):
        result = self.run_source(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, expected)

    def test_reads_all_element_types_and_empty_storage(self):
        self.assert_success('fn main() {\nlet a: int[] = [-2147483648, 2147483647]\n'
                            'let s: string[] = ["LAI", "100%"]\n'
                            'let b: bool[] = [false, a[1] > 0]\n'
                            'let e: int[] = []\nlet es: string[] = []\nlet eb: bool[] = []\n'
                            'print(a[0])\nprint(a[1])\nprint(s[1])\nprint(b[0])\nprint(b[1])\n}',
                            "-2147483648\n2147483647\n100%\n0\n1\n")

    def test_initializers_are_ordered_and_index_runs_once(self):
        self.assert_success('fn value(n: int) -> int {\nprint(n)\nreturn n\n}\n'
                            'fn main() {\nlet a: int[] = [value(10), value(20), value(30)]\n'
                            'print(a[value(1)])\n}', "10\n20\n30\n1\n20\n")

    def test_dynamic_bounds_fail_for_every_element_type(self):
        for kind, value in (("int", "42"), ("string", '"LAI"'), ("bool", "true")):
            for literal, length, index in ((f"[{value}]", 1, -1), (f"[{value}]", 1, 1), ("[]", 0, 0)):
                with self.subTest(kind=kind, index=index, length=length):
                    result = self.run_source(f"fn main() {{\nlet a: {kind}[] = {literal}\n"
                                             f"let i = {index}\nprint(a[i])\nprint(999)\n}}")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stderr,
                                     f"LAI runtime error: line 4: array index out of bounds: index {index}, length {length}\n")
                    self.assertEqual(result.stdout, "")

    def test_short_circuit_does_not_evaluate_dynamic_bad_index(self):
        self.assert_success('fn bad() -> int {\nprint(999)\nreturn 1\n}\n'
                            'fn main() {\nlet a: bool[] = [true]\n'
                            'print(false and a[bad()])\nprint(true or a[bad()])\n}', "0\n1\n")

    def test_initialization_stops_at_first_failure(self):
        result = self.run_source('fn value(n: int) -> int {\nprint(n)\nreturn n\n}\n'
                                 'fn main() {\nlet empty: int[] = []\nlet i = 0\n'
                                 'let a: int[] = [value(1), empty[i], value(999)]\n}')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "1\n")
        self.assertIn("line 8: array index out of bounds", result.stderr)

    def test_arrays_in_loops_and_early_return(self):
        self.assert_success('fn pick(n: int) -> int {\n'
                            'for i from 0 to n {\nlet a: int[] = [i, i + 10]\n'
                            'if i > 0 {\nreturn a[1]\n}\n}\nreturn -1\n}\n'
                            'fn main() {\nprint(pick(3))\nprint(pick(0))\n}', "11\n-1\n")

    def test_reads_inside_loop_conditions_and_compound_assignments(self):
        self.assert_success('fn main() {\nlet a: int[] = [2, 4]\nlet i = 0\n'
                            'while i < a[1] {\ni += a[0]\n}\n'
                            'i *= a[0]\ni /= a[0]\ni -= a[0]\ni %= a[0]\nprint(i)\n}', "0\n")

    def test_internal_names_and_same_named_functions_do_not_collide(self):
        self.assert_success('fn scores() -> int {\nreturn 7\n}\n'
                            'fn main() {\nlet __lai_internal_array_index = 0\n'
                            'let scores: int[] = [scores()]\n'
                            'let __lai_internal__array_storage_1: string[] = ["ok"]\n'
                            'print(scores[__lai_internal_array_index])\nprint(scores())\n'
                            'print(__lai_internal__array_storage_1[0])\n}', "7\n7\nok\n")

    def test_string_and_boolean_function_initializers(self):
        self.assert_success('fn name() -> string {\nprint(1)\nreturn "LAI"\n}\n'
                            'fn flag() -> bool {\nprint(2)\nreturn true\n}\n'
                            'fn main() {\nlet s: string[] = [name()]\n'
                            'let b: bool[] = [flag(), s[0] == "LAI"]\n'
                            'print(s[0])\nprint(b[0] and b[1])\n}', "1\n2\nLAI\n1\n")

    def test_nested_dynamic_indices_check_both_levels_and_run_once(self):
        prefix = ('fn index(n: int) -> int {\nprint(n)\nreturn n\n}\n'
                  'fn main() {\nlet a: int[] = [10, 20, 30]\n'
                  'let b: int[] = [2, 3]\n')
        self.assert_success(prefix + 'print(a[b[index(0)]])\n}', "0\n30\n")
        for index, error in ((1, "index 3, length 3"), (2, "index 2, length 2")):
            with self.subTest(index=index):
                result = self.run_source(prefix + f'print(a[b[index({index})]])\n}}')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, f"{index}\n")
                self.assertEqual(result.stderr,
                                 f"LAI runtime error: line 8: array index out of bounds: {error}\n")

    def test_index_arithmetic_errors_precede_array_access(self):
        for value, index, error in (
            (2147483647, "i + 1", "integer addition overflow"),
            (-2147483648, "i - 1", "integer subtraction overflow"),
            (2147483647, "i * 2", "integer multiplication overflow"),
            (-2147483648, "-i", "integer unary negation overflow"),
            (0, "1 / i", "division by zero"),
            (0, "1 % i", "modulo by zero"),
        ):
            with self.subTest(index=index):
                result = self.run_source(f"fn main() {{\nlet a: int[] = [1]\n"
                                         f"let i = {value}\nprint(a[{index}])\n}}")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, f"LAI runtime error: line 4: {error}\n")

    def test_array_reads_in_for_bounds_are_ordered_and_evaluated_once(self):
        self.assert_success('fn trace(i: int) -> int {\nprint(i)\nreturn i\n}\n'
                            'fn main() {\nlet bounds: int[] = [0, 3, 1]\n'
                            'for i from bounds[trace(0)] to bounds[trace(1)] step bounds[trace(2)] {\n'
                            'print(i + 10)\n}\n}', "0\n1\n2\n10\n11\n12\n")


if __name__ == "__main__":
    unittest.main()
