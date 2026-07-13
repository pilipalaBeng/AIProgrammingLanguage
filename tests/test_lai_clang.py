import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lai_clang import build_with_clang
from lai_core import LaiCompileError


class LaiClangTests(unittest.TestCase):
    def test_reports_missing_clang(self):
        with patch("lai_clang.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(LaiCompileError) as context:
                build_with_clang(Path("main.ll"), Path("main.exe"))

        self.assertEqual(
            str(context.exception),
            "failed to run clang: clang was not found. "
            "Open the x64 Native Tools Command Prompt for VS, or add clang to Path.",
        )

    def test_preserves_clang_failure_details(self):
        result = Mock(returncode=1, stdout="compiler stdout", stderr="compiler stderr")
        with patch("lai_clang.subprocess.run", return_value=result):
            with self.assertRaises(LaiCompileError) as context:
                build_with_clang(Path("main.ll"), Path("main.exe"))

        self.assertEqual(
            str(context.exception),
            "clang failed.\n"
            "Command: clang main.ll -o main.exe\n"
            "Tip: run this from the x64 Native Tools Command Prompt for VS.\n"
            "stdout:\ncompiler stdout\n"
            "stderr:\ncompiler stderr",
        )

    def test_invokes_clang_with_generated_source_and_executable(self):
        result = Mock(returncode=0, stdout="", stderr="")
        with patch("lai_clang.subprocess.run", return_value=result) as run:
            build_with_clang(Path("main.ll"), Path("main.exe"))

        run.assert_called_once_with(
            ["clang", "main.ll", "-o", "main.exe"],
            capture_output=True,
            text=True,
            check=False,
        )
