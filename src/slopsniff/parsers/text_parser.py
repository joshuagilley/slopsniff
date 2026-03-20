import hashlib
import re
from pathlib import Path

from ..models import FunctionInfo

_FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function"),
    # Arrow methods inside class bodies: methodName = () =>
    re.compile(r"^\s*(\w+)\s*=\s*(?:async\s+)?\("),
]


def _sha256(lines: list[str]) -> str:
    normalized = "\n".join(ln.strip() for ln in lines if ln.strip())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _find_block_end(lines: list[str], start_idx: int) -> int:
    """Return the 0-based exclusive end index of the brace-delimited block."""
    depth = 0
    for i in range(start_idx, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if depth > 0 and i > start_idx:
            pass
        if depth <= 0 and i >= start_idx:
            return i + 1
    return len(lines)


def parse_text(path: Path, lines: list[str]) -> list[FunctionInfo]:
    functions: list[FunctionInfo] = []
    i = 0
    while i < len(lines):
        for pattern in _FUNCTION_PATTERNS:
            match = pattern.match(lines[i])
            if match:
                name = match.group(1)
                end_idx = _find_block_end(lines, i)
                body_hash = _sha256(lines[i:end_idx])
                functions.append(
                    FunctionInfo(
                        name=name,
                        file_path=str(path),
                        line_start=i + 1,
                        line_end=end_idx,
                        body_hash=body_hash,
                    )
                )
                i = end_idx
                break
        else:
            i += 1
    return functions
