import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import lai_c_backend
import lai_compiler
from lai_backend import Backend
from lai_c_backend import C_BACKEND, build_c, generate_c
from lai_compiler import compile_file, compile_source
from lai_core import LaiCompileError


class LaiBackendTests(unittest.TestCase):
    def test_backend_is_an_immutable_function_descriptor(self):
        emit = Mock(return_value="output")
        build = Mock()
        backend = Backend("fake", ".ir", emit, build)

        self.assertEqual(backend.name, "fake")
        self.assertEqual(backend.source_suffix, ".ir")
        self.assertIs(backend.emit, emit)
        self.assertIs(backend.build, build)
        with self.assertRaises(FrozenInstanceError):
            backend.name = "changed"

    def test_c_backend_descriptor_uses_c_functions(self):
        self.assertEqual(C_BACKEND.name, "c")
        self.assertEqual(C_BACKEND.source_suffix, ".c")
        self.assertIs(C_BACKEND.build, build_c)

    def test_build_c_reports_missing_clang(self):
        with patch("lai_clang.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(
                LaiCompileError,
                "failed to run clang: clang was not found",
            ):
                build_c(Path("main.c"), Path("main.exe"))

    def test_build_c_preserves_clang_failure_details(self):
        result = Mock(returncode=1, stdout="compiler stdout", stderr="compiler stderr")
        with patch("lai_clang.subprocess.run", return_value=result):
            with self.assertRaises(LaiCompileError) as context:
                build_c(Path("main.c"), Path("main.exe"))

        message = str(context.exception)
        self.assertIn("clang failed.", message)
        self.assertIn("Command: clang main.c -o main.exe", message)
        self.assertIn("stdout:\ncompiler stdout", message)
        self.assertIn("stderr:\ncompiler stderr", message)

    def test_compile_source_can_emit_with_an_injected_backend(self):
        emit = Mock(return_value="fake output")
        backend = Backend("fake", ".fake", emit, Mock())

        output = compile_source('fn main() {\n    print("Hello")\n}', backend)

        self.assertEqual(output, "fake output")
        emit.assert_called_once()

    def test_compile_source_checks_before_backend_emission(self):
        emit = Mock(return_value="must not be returned")
        backend = Backend("fake", ".fake", emit, Mock())

        with self.assertRaisesRegex(LaiCompileError, "unknown variable: missing"):
            compile_source("fn main() {\n    print(missing)\n}", backend)

        emit.assert_not_called()

    def test_default_c_compile_source_checks_once_without_backend_recheck(self):
        source = 'fn main() {\n    print("Hello")\n}'

        with patch(
            "lai_compiler.check_program", wraps=lai_compiler.check_program
        ) as compiler_checker, patch(
            "lai_c_backend.check_program", wraps=lai_c_backend.check_program
        ) as c_backend_checker:
            output = compile_source(source)

        self.assertEqual(compiler_checker.call_count, 1)
        self.assertEqual(c_backend_checker.call_count, 0)
        self.assertIn("#include <stdio.h>", output)
        self.assertIn('printf("Hello\\n");', output)
        self.assertIn("int main(void)", output)

    def test_compile_file_uses_backend_suffix_emitter_and_builder(self):
        emit = Mock(return_value="fake artifact")
        build = Mock()
        backend = Backend("fake", ".fake", emit, build)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "sample.ly"
            build_dir = root / "build"
            source_path.write_text("fn main() {\n}\n", encoding="utf-8")

            artifact_path, exe_path = compile_file(source_path, build_dir, backend)

            self.assertEqual(artifact_path, build_dir / "sample.fake")
            self.assertEqual(artifact_path.read_text(encoding="utf-8"), "fake artifact")
            self.assertEqual(exe_path, build_dir / "sample.exe")
            build.assert_called_once_with(artifact_path, exe_path)


if __name__ == "__main__":
    unittest.main()
