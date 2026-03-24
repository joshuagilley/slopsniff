from pathlib import Path
from typing import Annotated, Literal

import typer

from . import scanner as _scanner
from .config import Config, load_config_overrides
from .reporters import json_reporter
from .reporters import terminal as terminal_reporter

app = typer.Typer(
    name="slopsniff",
    help="Catch AI slop and code quality drift before it hardens into tech debt.",
    no_args_is_help=True,
)


def _resolve_scan_root(path: str) -> Path:
    root = Path(path).resolve()
    if not root.exists():
        typer.echo(f"Error: path '{path}' does not exist.", err=True)
        raise typer.Exit(1)
    return root if root.is_dir() else root.parent


def _build_config(
    scan_root: Path,
    fail_threshold: int | None,
    verbose: bool | None,
    max_file_lines: int | None,
    max_function_lines: int | None,
) -> Config:
    config = Config()
    overrides = load_config_overrides(scan_root) or {}

    if "include" in overrides:
        config.include_rules = overrides["include"]  # type: ignore[assignment]
    if "fail-threshold" in overrides:
        config.fail_threshold = overrides["fail-threshold"]  # type: ignore[assignment]
    if "max-file-lines-warning" in overrides:
        config.max_file_lines_warning = overrides["max-file-lines-warning"]  # type: ignore[assignment]
    if "max-file-lines-high" in overrides:
        config.max_file_lines_high = overrides["max-file-lines-high"]  # type: ignore[assignment]
    if "max-function-lines-warning" in overrides:
        config.max_function_lines_warning = overrides["max-function-lines-warning"]  # type: ignore[assignment]
    if "max-function-lines-high" in overrides:
        config.max_function_lines_high = overrides["max-function-lines-high"]  # type: ignore[assignment]
    if "include-extensions" in overrides:
        config.include_extensions = overrides["include-extensions"]  # type: ignore[assignment]
    if "large-file-extensions" in overrides:
        config.large_file_extensions = frozenset(overrides["large-file-extensions"])  # type: ignore[arg-type]
    if "exclude-dirs" in overrides:
        config.exclude_dirs = overrides["exclude-dirs"]  # type: ignore[assignment]
    if "exclude-files" in overrides:
        config.exclude_files = overrides["exclude-files"]  # type: ignore[assignment]
    if "exclude-severities" in overrides:
        config.exclude_severities = frozenset(overrides["exclude-severities"])  # type: ignore[arg-type]
    if "verbose" in overrides:
        config.verbose = overrides["verbose"]  # type: ignore[assignment]

    if fail_threshold is not None:
        config.fail_threshold = fail_threshold
    if verbose is not None:
        config.verbose = verbose
    if max_file_lines is not None:
        config.max_file_lines_warning = max_file_lines
    if max_function_lines is not None:
        config.max_function_lines_warning = max_function_lines
    return config


def _render_result(
    result: _scanner.ScanResult,
    output_format: Literal["terminal", "json"],
    verbose: bool,
) -> None:
    if output_format == "json":
        typer.echo(json_reporter.report(result))
        return
    terminal_reporter.report(result, verbose=verbose)


def _resolve_git_diff_ref(branch: bool, changed_since: str | None) -> str | None:
    if branch and changed_since is not None:
        typer.echo("Error: use either --branch or --changed-since, not both.", err=True)
        raise typer.Exit(1)
    if branch:
        return "main"
    if changed_since is None:
        return None
    ref = changed_since.strip() or None
    if ref is None:
        typer.echo("Error: --changed-since requires a non-empty ref.", err=True)
        raise typer.Exit(1)
    return ref


@app.command()
def scan(
    path: Annotated[str, typer.Argument(help="Path to the directory to scan")] = ".",
    fail_threshold: Annotated[
        int | None, typer.Option("--fail-threshold", "-t", help="Score at which CI fails")
    ] = None,
    format: Annotated[
        Literal["terminal", "json"],
        typer.Option("--format", "-f", help="Output format: terminal or json"),
    ] = "terminal",
    verbose: Annotated[
        bool | None,
        typer.Option("--verbose/--no-verbose", "-v", help="Show score per finding"),
    ] = None,
    max_file_lines: Annotated[
        int | None,
        typer.Option("--max-file-lines", help="Override file line warning threshold"),
    ] = None,
    max_function_lines: Annotated[
        int | None,
        typer.Option("--max-function-lines", help="Override function line warning threshold"),
    ] = None,
    branch: Annotated[
        bool,
        typer.Option("--branch", help="Only files changed vs main (same as --changed-since main)"),
    ] = False,
    changed_since: Annotated[
        str | None,
        typer.Option(
            "--changed-since",
            metavar="REF",
            help="Only files changed vs ref (git diff REF --name-only --diff-filter=ACMR).",
        ),
    ] = None,
) -> None:
    """Scan for slop. Examples: slopsniff .  slopsniff . --branch  slopsniff . -f json."""
    target = _resolve_scan_root(path)
    ref = _resolve_git_diff_ref(branch, changed_since)
    try:
        config = _build_config(target, fail_threshold, verbose, max_file_lines, max_function_lines)
        result = _scanner.scan(target, config, changed_since=ref)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    _render_result(result, format, verbose)
    if not result.passed:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
