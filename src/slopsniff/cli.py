from pathlib import Path
from typing import Annotated, Literal

import typer

from . import scanner as _scanner
from .config import Config
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
    fail_threshold: int,
    verbose: bool,
    max_file_lines: int | None,
    max_function_lines: int | None,
) -> Config:
    config = Config(fail_threshold=fail_threshold, verbose=verbose)
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


@app.command()
def scan(
    path: Annotated[str, typer.Argument(help="Path to the directory to scan")] = ".",
    fail_threshold: Annotated[
        int, typer.Option("--fail-threshold", "-t", help="Score at which CI fails")
    ] = 20,
    format: Annotated[
        Literal["terminal", "json"],
        typer.Option("--format", "-f", help="Output format: terminal or json"),
    ] = "terminal",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show score per finding")
    ] = False,
    max_file_lines: Annotated[
        int | None,
        typer.Option("--max-file-lines", help="Override file line warning threshold"),
    ] = None,
    max_function_lines: Annotated[
        int | None,
        typer.Option("--max-function-lines", help="Override function line warning threshold"),
    ] = None,
) -> None:
    """Scan a codebase for slop patterns.

    Examples:

      slopsniff .

      slopsniff ./src --fail-threshold 30

      slopsniff . --format json
    """
    target = _resolve_scan_root(path)
    config = _build_config(fail_threshold, verbose, max_file_lines, max_function_lines)
    result = _scanner.scan(target, config)
    _render_result(result, format, verbose)

    if not result.passed:
        raise typer.Exit(1)
