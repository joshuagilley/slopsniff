from pathlib import Path
from typing import Annotated

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


@app.command()
def scan(
    path: Annotated[
        str, typer.Argument(help="Path to the directory to scan")
    ] = ".",
    fail_threshold: Annotated[
        int, typer.Option("--fail-threshold", "-t", help="Score at which CI fails")
    ] = 20,
    format: Annotated[
        str,
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
        typer.Option(
            "--max-function-lines", help="Override function line warning threshold"
        ),
    ] = None,
) -> None:
    """Scan a codebase for slop patterns.

    Examples:

      slopsniff .

      slopsniff ./src --fail-threshold 30

      slopsniff . --format json
    """
    root = Path(path).resolve()
    if not root.exists():
        typer.echo(f"Error: path '{path}' does not exist.", err=True)
        raise typer.Exit(1)

    config = Config(fail_threshold=fail_threshold, verbose=verbose)
    if max_file_lines is not None:
        config.max_file_lines_warning = max_file_lines
    if max_function_lines is not None:
        config.max_function_lines_warning = max_function_lines

    target = root if root.is_dir() else root.parent
    result = _scanner.scan(target, config)

    if format == "json":
        typer.echo(json_reporter.report(result))
    else:
        terminal_reporter.report(result, verbose=verbose)

    if not result.passed:
        raise typer.Exit(1)
