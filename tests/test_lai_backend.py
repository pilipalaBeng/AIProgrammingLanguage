import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock, patch

from lai_backend import Backend
from lai_c_backend import C_BACKEND, build_c, generate_c
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
        with patch("lai_c_backend.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(
                LaiCompileError,
                "failed to run clang: clang was not found",
            ):
                build_c(Path("main.c"), Path("main.exe"))

    def test_build_c_preserves_clang_failure_details(self):
        result = Mock(returncode=1, stdout="compiler stdout", stderr="compiler stderr")
        with patch("lai_c_backend.subprocess.run", return_value=result):
            with self.assertRaises(LaiCompileError) as context:
                build_c(Path("main.c"), Path("main.exe"))

        message = str(context.exception)
        self.assertIn("clang failed.", message)
        self.assertIn("Command: clang main.c -o main.exe", message)
        self.assertIn("stdout:\ncompiler stdout", message)
        self.assertIn("stderr:\ncompiler stderr", message)


if __name__ == "__main__":
    unittest.main()
