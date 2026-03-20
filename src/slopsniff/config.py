from dataclasses import dataclass, field


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
            ".md",
            ".mdx",
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
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ]
    )
    verbose: bool = False
