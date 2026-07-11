from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lai_ast import Program


@dataclass(frozen=True)
class Backend:
    name: str
    source_suffix: str
    emit: Callable[[Program], str]
    build: Callable[[Path, Path], None]
