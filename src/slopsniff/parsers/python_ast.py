import ast
import hashlib
import textwrap
from pathlib import Path

from ..models import FunctionInfo


def _normalize_body(lines: list[str], line_start: int, line_end: int) -> str:
    """Extract and normalize function body lines for stable hashing.

    line_start and line_end are 1-indexed (matching ast node values).
    """
    body_lines = lines[line_start - 1 : line_end]
    dedented = textwrap.dedent("\n".join(body_lines))
    return "\n".join(ln.strip() for ln in dedented.splitlines() if ln.strip())


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def parse_python(path: Path, lines: list[str]) -> list[FunctionInfo]:
    source = "\n".join(lines)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    functions: list[FunctionInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.end_lineno is None:
                continue
            body_text = _normalize_body(lines, node.lineno, node.end_lineno)
            functions.append(
                FunctionInfo(
                    name=node.name,
                    file_path=str(path),
                    line_start=node.lineno,
                    line_end=node.end_lineno,
                    body_hash=_sha256(body_text),
                )
            )
    return functions
