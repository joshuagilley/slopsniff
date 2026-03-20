from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
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


def _format_location(finding: Finding) -> str:
    loc = finding.file_path
    if finding.line_start is not None:
        loc += f":{finding.line_start}"
        if finding.line_end is not None and finding.line_end != finding.line_start:
            loc += f"-{finding.line_end}"
    return loc


def _summary_panel(result: ScanResult, status: str) -> Panel:
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="dim", justify="right")
    grid.add_column()

    grid.add_row("Files scanned", str(result.files_scanned))
    grid.add_row("Total score", str(result.total_score))
    status_style = _STATUS_STYLE.get(status, "white")
    grid.add_row("Status", Text(status.upper(), style=status_style))

    return Panel(
        grid,
        title="[bold white]SlopSniff[/bold white]",
        title_align="left",
        border_style="bright_magenta",
        padding=(1, 2),
    )


def report(result: ScanResult, verbose: bool = False) -> None:
    console = Console()
    status = grade(result.total_score)

    console.print()
    console.print(_summary_panel(result, status))
    console.print()

    if not result.findings:
        console.print(
            Panel(
                Text("No issues found.", style="bold green"),
                border_style="green",
            )
        )
        console.print()
        return

    sorted_findings = sorted(
        result.findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 3), f.file_path),
    )

    console.print(Rule("[dim]Findings[/dim]", style="bright_magenta"))
    console.print()

    for finding in sorted_findings:
        sev = finding.severity.lower()
        style = _SEVERITY_STYLE.get(sev, "white")
        label = f"[{finding.severity.upper()}] "
        console.print(Text.assemble((label, style), (finding.rule_id, "cyan")))
        console.print(Text(f"  {_format_location(finding)}", style="dim"))
        console.print(Text(f"  {escape(finding.message)}"))
        if verbose:
            console.print(Text(f"  score: +{finding.score}", style="dim italic"))
        console.print()
