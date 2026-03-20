from pathlib import Path

from slopsniff.config import Config
from slopsniff.models import FileContext
from slopsniff.rules.large_file import LargeFileRule


def _ctx(path: Path, line_count: int) -> FileContext:
    return FileContext(path=path, lines=["x = 1"] * line_count, language="python")


def test_no_finding_below_warning_threshold(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    assert rule.run(_ctx(tmp_path / "small.py", 100)) == []


def test_medium_finding_at_warning_threshold(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    findings = rule.run(_ctx(tmp_path / "medium.py", 400))
    assert len(findings) == 1
    assert findings[0].severity == "medium"
    assert findings[0].rule_id == "large-file"
    assert findings[0].score == 5


def test_medium_finding_below_high_threshold(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    findings = rule.run(_ctx(tmp_path / "medium.py", 799))
    assert len(findings) == 1
    assert findings[0].severity == "medium"


def test_high_finding_at_high_threshold(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    findings = rule.run(_ctx(tmp_path / "large.py", 800))
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].score == 10


def test_custom_thresholds(tmp_path: Path) -> None:
    config = Config(max_file_lines_warning=100, max_file_lines_high=200)
    rule = LargeFileRule(config)
    assert rule.run(_ctx(tmp_path / "a.py", 99)) == []
    assert rule.run(_ctx(tmp_path / "b.py", 100))[0].severity == "medium"
    assert rule.run(_ctx(tmp_path / "c.py", 200))[0].severity == "high"


def test_skips_markdown_even_when_huge(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    assert rule.run(_ctx(tmp_path / "readme.md", 10_000)) == []


def test_skips_html_even_when_huge(tmp_path: Path) -> None:
    rule = LargeFileRule(Config())
    assert rule.run(_ctx(tmp_path / "page.html", 10_000)) == []
