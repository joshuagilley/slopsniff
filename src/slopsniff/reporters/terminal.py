from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.markup import escape
from rich.text import Text

from ..models import Finding, ScanResult
from ..scoring import grade

_SEVERITY_STYLE = {
    "high": "bold red",
    "medium": "bold yellow",
    "low": "bold blue",
}
_STATUS_STYLE = {
    "healthy": "bold green",
    "warning": "bold yellow",
    "fail": "bold red",
}
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _line_range(finding: Finding) -> str:
    if finding.line_start is None:
        return "?"
    if finding.line_end is None or finding.line_end == finding.line_start:
        return str(finding.line_start)
    return f"{finding.line_start}-{finding.line_end}"


def _summary_line(result: ScanResult, status: str) -> Text:
    n = len(result.findings)
    issues = "issue" if n == 1 else "issues"
    status_style = _STATUS_STYLE.get(status, "white")
    return Text.assemble(
        ("slopsniff ", "bold"),
        (f"{result.files_scanned} files  ", ""),
        (f"{n} {issues}  ", "dim"),
        (f"score {result.total_score}  ", ""),
        (status.upper(), status_style),
    )


def _sort_key_path(f: Finding) -> tuple[str, str, int, str]:
    return (
        _display_path(Path(f.file_path).parent),
        Path(f.file_path).name,
        _SEVERITY_ORDER.get(f.severity.lower(), 3),
        f.rule_id,
    )


def _print_finding_line(console: Console, finding: Finding, verbose: bool) -> None:
    sev = finding.severity.lower()
    style = _SEVERITY_STYLE.get(sev, "white")
    loc = _line_range(finding)
    msg = escape(finding.message)
    console.print(
        Text.assemble(
            "    ",
            (loc, "dim"),
            " ",
            (f"[{finding.severity.upper()}]", style),
            " ",
            (finding.rule_id, "white"),
            "  ",
            (msg, "default"),
        )
    )
    if verbose:
        console.print(Text(f"      (+{finding.score})", style="dim italic"))


def _print_grouped_findings(console: Console, findings: list[Finding], verbose: bool) -> None:
    by_dir: dict[str, list[Finding]] = defaultdict(list)
    for f in findings:
        by_dir[str(Path(f.file_path).resolve().parent)].append(f)

    for dir_path in sorted(by_dir.keys(), key=lambda p: _display_path(Path(p))):
        console.print(Text(f"{_display_path(Path(dir_path))}/", style="bold dim"))
        by_file: dict[str, list[Finding]] = defaultdict(list)
        for f in by_dir[dir_path]:
            by_file[f.file_path].append(f)
        for file_path in sorted(by_file.keys(), key=lambda p: Path(p).name):
            console.print(Text(f"  {Path(file_path).name}", style="cyan"))
            for finding in sorted(
                by_file[file_path],
                key=lambda f: (
                    _SEVERITY_ORDER.get(f.severity.lower(), 3),
                    f.line_start or 0,
                    f.rule_id,
                ),
            ):
                _print_finding_line(console, finding, verbose)


def report(result: ScanResult, verbose: bool = False) -> None:
    console = Console()
    status = grade(result.total_score)
    console.print(_summary_line(result, status))
    if not result.findings:
        console.print(Text("No issues.", style="green"))
        return
    ordered = sorted(result.findings, key=_sort_key_path)
    _print_grouped_findings(console, ordered, verbose)
