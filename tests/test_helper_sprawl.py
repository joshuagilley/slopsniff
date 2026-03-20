from pathlib import Path

from slopsniff.models import FileContext, FunctionInfo
from slopsniff.rules.helper_sprawl import HelperSprawlRule


def _ctx(path: Path, functions: list[FunctionInfo] | None = None) -> FileContext:
    return FileContext(
        path=path, lines=[], language="python", functions=functions or []
    )


def _fn(name: str, path: str, line: int = 1) -> FunctionInfo:
    return FunctionInfo(name=name, file_path=path, line_start=line, line_end=line + 5, body_hash="h")


def test_flags_utils_filename(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    findings = rule.run(_ctx(tmp_path / "utils.py"))
    assert len(findings) == 1
    assert findings[0].rule_id == "helper-sprawl"
    assert findings[0].severity == "low"


def test_flags_helpers_filename(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    findings = rule.run(_ctx(tmp_path / "helpers.py"))
    assert len(findings) == 1


def test_flags_common_filename(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    findings = rule.run(_ctx(tmp_path / "common.py"))
    assert len(findings) == 1


def test_no_flag_for_specific_filename(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    assert rule.run(_ctx(tmp_path / "auth_service.py")) == []
    assert rule.run(_ctx(tmp_path / "database.py")) == []


def test_flags_versioned_function_names(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    ctx_a = _ctx(tmp_path / "a.py", [_fn("format_data", "a.py")])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("format_data_v2", "b.py")])
    findings = rule.run_cross_file([ctx_a, ctx_b])
    assert len(findings) == 1
    assert findings[0].rule_id == "helper-sprawl"
    assert findings[0].severity == "medium"


def test_flags_legacy_variants(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    ctx_a = _ctx(tmp_path / "a.py", [_fn("send_email", "a.py")])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("send_email_old", "b.py")])
    findings = rule.run_cross_file([ctx_a, ctx_b])
    assert len(findings) == 1


def test_no_flag_for_unique_function_names(tmp_path: Path) -> None:
    rule = HelperSprawlRule()
    ctx_a = _ctx(tmp_path / "a.py", [_fn("parse_user", "a.py")])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("parse_order", "b.py")])
    assert rule.run_cross_file([ctx_a, ctx_b]) == []
