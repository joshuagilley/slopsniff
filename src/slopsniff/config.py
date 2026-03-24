import json
from dataclasses import dataclass, field
from pathlib import Path


def _default_large_file_extensions() -> frozenset[str]:
    """Extensions where line-count heuristics match source code (not prose/docs)."""
    return frozenset({".py", ".js", ".ts", ".tsx", ".jsx", ".vue"})


@dataclass
class Config:
    max_file_lines_warning: int = 400
    max_file_lines_high: int = 800
    max_function_lines_warning: int = 50
    max_function_lines_high: int = 100
    fail_threshold: int = 20
    include_extensions: list[str] = field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".vue",
            ".html",
        ]
    )
    large_file_extensions: frozenset[str] = field(default_factory=_default_large_file_extensions)
    exclude_dirs: list[str] = field(
        default_factory=lambda: [
            ".git",
            "node_modules",
            ".nuxt",
            "dist",
            "build",
            ".venv",
            "coverage",
            "tests",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ]
    )
    verbose: bool = False
    include_rules: list[str] | None = None


def _normalize_include_list(values: list[object]) -> list[str]:
    include: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError("Config 'include' entries must be strings")
        cleaned = value.strip()
        if cleaned:
            include.append(cleaned)
    return include


def _extract_json_include(path: Path) -> list[str] | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    include = data.get("include")
    if include is None:
        return None
    if not isinstance(include, list):
        raise ValueError("Config 'include' must be an array")
    return _normalize_include_list(include)


def load_include_rules(scan_root: Path) -> list[str] | None:
    json_path = scan_root / "slopsniff.json"
    if json_path.exists():
        return _extract_json_include(json_path)
    return None
