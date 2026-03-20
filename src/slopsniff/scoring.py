from .models import Finding

SEVERITY_SCORES: dict[str, int] = {"low": 2, "medium": 5, "high": 10}


def compute_score(findings: list[Finding]) -> int:
    return sum(f.score for f in findings)


def grade(score: int) -> str:
    if score < 10:
        return "healthy"
    if score < 20:
        return "warning"
    return "fail"
