import subprocess
from pathlib import Path

from lai_core import LaiCompileError


def build_with_clang(source_path: Path, exe_path: Path) -> None:
    command = ["clang", str(source_path), "-o", str(exe_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise LaiCompileError(
            "failed to run clang: clang was not found. "
            "Open the x64 Native Tools Command Prompt for VS, or add clang to Path."
        ) from exc

    if result.returncode != 0:
        details = [
            "clang failed.",
            f"Command: {' '.join(command)}",
            "Tip: run this from the x64 Native Tools Command Prompt for VS.",
        ]
        if result.stdout.strip():
            details.append(f"stdout:\n{result.stdout.rstrip()}")
        if result.stderr.strip():
            details.append(f"stderr:\n{result.stderr.rstrip()}")
        raise LaiCompileError("\n".join(details))
