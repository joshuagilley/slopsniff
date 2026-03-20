from pathlib import Path

from slopsniff.config import Config
from slopsniff.models import FileContext, FunctionInfo
from slopsniff.rules.large_function import LargeFunctionRule


def _fn(name: str, start: int, end: int, path: str = "a.py") -> FunctionInfo:
    return FunctionInfo(name=name, file_path=path, line_start=start, line_end=end, body_hash="x")


def _ctx(path: Path, functions: list[FunctionInfo]) -> FileContext:
    return FileContext(path=path, lines=[], language="python", functions=functions)


def test_no_finding_for_small_function(tmp_path: Path) -> None:
    rule = LargeFunctionRule(Config())
    ctx = _ctx(tmp_path / "a.py", [_fn("tiny", 1, 10)])
    assert rule.run(ctx) == []


def test_medium_finding_at_warning_threshold(tmp_path: Path) -> None:
    rule = LargeFunctionRule(Config())
    # 50 lines: line 1 to line 50 = 50 lines
    ctx = _ctx(tmp_path / "a.py", [_fn("medium_fn", 1, 50)])
    findings = rule.run(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].rule_id == "large-function"
    assert findings[0].score == 5


def test_high_finding_at_high_threshold(tmp_path: Path) -> None:
    rule = LargeFunctionRule(Config())
    ctx = _ctx(tmp_path / "a.py", [_fn("big_fn", 1, 100)])
    findings = rule.run(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].score == 10


def test_multiple_functions_independent(tmp_path: Path) -> None:
    rule = LargeFunctionRule(Config())
    ctx = _ctx(
        tmp_path / "a.py",
        [
            _fn("small", 1, 10),
            _fn("medium", 20, 70),
            _fn("large", 80, 200),
        ],
    )
    findings = rule.run(ctx)
    assert len(findings) == 2
    severities = {f.severity for f in findings}
    assert "medium" in severities
    assert "high" in severities


def test_line_numbers_are_propagated(tmp_path: Path) -> None:
    rule = LargeFunctionRule(Config())
    ctx = _ctx(tmp_path / "a.py", [_fn("fn", 42, 150)])
    findings = rule.run(ctx)
    assert findings[0].line_start == 42
    assert findings[0].line_end == 150
