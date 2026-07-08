import re


class LaiCompileError(Exception):
    pass


NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
