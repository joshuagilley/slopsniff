from ..models import Finding, ScanResult
from ..scoring import grade

_SEVERITY_COLOR = {
    "high": "\033[91m",    # bright red
    "medium": "\033[93m",  # bright yellow
    "low": "\033[94m",     # bright blue
}
_STATUS_COLOR = {
    "healthy": "\033[92m",  # green
    "warning": "\033[93m",  # yellow
    "fail": "\033[91m",     # red
}
_RESET = "\033[0m"
_BOLD = "\033[1m"
_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _severity_tag(severity: str) -> str:
    color = _SEVERITY_COLOR.get(severity, "")
    return f"{color}[{severity.upper()}]{_RESET}"


def _format_location(finding: Finding) -> str:
    loc = finding.file_path
    if finding.line_start is not None:
        loc += f":{finding.line_start}"
        if finding.line_end is not None and finding.line_end != finding.line_start:
            loc += f"-{finding.line_end}"
    return loc


def report(result: ScanResult, verbose: bool = False) -> None:
    status = grade(result.total_score)
    status_color = _STATUS_COLOR.get(status, "")

    print(f"\n{_BOLD}SlopSniff Report{_RESET}")
    print("=" * 40)
    print(f"Files scanned:  {result.files_scanned}")
    print(f"Total score:    {result.total_score}")
    print(f"Status:         {status_color}{status.upper()}{_RESET}")
    print()

    if not result.findings:
        print(f"\033[92mNo issues found.\033[0m\n")
        return

    sorted_findings = sorted(
        result.findings,
        key=lambda f: (_SEVERITY_ORDER.get(f.severity, 3), f.file_path),
    )

    for finding in sorted_findings:
        print(f"{_severity_tag(finding.severity)} {finding.rule_id}")
        print(f"  {_format_location(finding)}")
        print(f"  {finding.message}")
        if verbose:
            print(f"  score: +{finding.score}")
        print()
