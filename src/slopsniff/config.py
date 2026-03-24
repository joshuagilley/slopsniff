import json
from dataclasses import dataclass, field
from pathlib import Path


def _default_large_file_extensions() -> frozenset[str]:
    """Extensions where line-count heuristics match source code (not prose/docs)."""
    return frozenset({".py", ".js", ".ts", ".tsx", ".jsx", ".vue"})


_VALID_SEVERITIES = frozenset({"low", "medium", "high"})

_CONFIG_ALLOWED_KEYS = frozenset(
    {
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
        "exclude-severities",
        "verbose",
    }
)

_CONFIG_INT_KEYS = frozenset(
    {
        "fail-threshold",
        "max-file-lines-warning",
        "max-file-lines-high",
        "max-function-lines-warning",
        "max-function-lines-high",
    }
)


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
    exclude_severities: frozenset[str] = field(default_factory=frozenset)
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


def _parse_config_value(key: str, value: object) -> object:
    if key in _CONFIG_INT_KEYS:
        if not isinstance(value, int):
            raise ValueError(f"Config '{key}' must be an integer")
        return value
    if key == "verbose":
        if not isinstance(value, bool):
            raise ValueError("Config 'verbose' must be a boolean")
        return value
    if key == "exclude-severities":
        if not isinstance(value, list):
            raise ValueError("Config 'exclude-severities' must be an array")
        raw = _normalize_str_list(value, "exclude-severities")
        normalized = [s.lower() for s in raw]
        invalid = [s for s in normalized if s not in _VALID_SEVERITIES]
        if invalid:
            bad = ", ".join(sorted(set(invalid)))
            raise ValueError(
                f"Config 'exclude-severities' must be only low, medium, high; invalid: {bad}"
            )
        return normalized
    if not isinstance(value, list):
        raise ValueError(f"Config '{key}' must be an array")
    return _normalize_str_list(value, key)


def load_config_overrides(scan_root: Path) -> dict[str, object] | None:
    json_path = scan_root / "slopsniff.json"
    if not json_path.exists():
        return None

    data = _extract_json_config(json_path)
    unknown = set(data) - _CONFIG_ALLOWED_KEYS
    if unknown:
        keys = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown config key(s): {keys}")

    return {key: _parse_config_value(key, value) for key, value in data.items()}
