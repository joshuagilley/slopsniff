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
    exclude_files: list[str] = field(default_factory=list)
    verbose: bool = False
    include_rules: list[str] | None = None


def _normalize_str_list(values: list[object], key: str) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"Config '{key}' entries must be strings")
        cleaned = value.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _extract_json_config(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def load_config_overrides(scan_root: Path) -> dict[str, object] | None:
    json_path = scan_root / "slopsniff.json"
    if not json_path.exists():
        return None

    data = _extract_json_config(json_path)
    allowed = {
        "include",
        "fail-threshold",
        "max-file-lines-warning",
        "max-file-lines-high",
        "max-function-lines-warning",
        "max-function-lines-high",
        "include-extensions",
        "large-file-extensions",
        "exclude-dirs",
        "exclude-files",
        "verbose",
    }

    unknown = set(data) - allowed
    if unknown:
        keys = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown config key(s): {keys}")

    parsed: dict[str, object] = {}
    for key, value in data.items():
        if key in {
            "fail-threshold",
            "max-file-lines-warning",
            "max-file-lines-high",
            "max-function-lines-warning",
            "max-function-lines-high",
        }:
            if not isinstance(value, int):
                raise ValueError(f"Config '{key}' must be an integer")
            parsed[key] = value
        elif key == "verbose":
            if not isinstance(value, bool):
                raise ValueError("Config 'verbose' must be a boolean")
            parsed[key] = value
        else:
            if not isinstance(value, list):
                raise ValueError(f"Config '{key}' must be an array")
            parsed[key] = _normalize_str_list(value, key)

    return parsed
