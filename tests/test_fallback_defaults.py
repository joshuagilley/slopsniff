from pathlib import Path

from slopsniff.models import FileContext
from slopsniff.rules.fallback_defaults import FallbackDefaultsRule


def _ctx(path: Path, lines: list[str]) -> FileContext:
    return FileContext(path=path, lines=lines, language="text")


def test_detects_python_getenv_fallback(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(_ctx(tmp_path / "settings.py", ['timeout = os.getenv("TIMEOUT", 0)']))
    assert len(findings) == 1
    assert findings[0].rule_id == "fallback-defaults"
    assert findings[0].severity == "medium"
    assert findings[0].line_start == 1
    assert findings[0].score == 4
    assert "primitive sentinel" in findings[0].message


def test_detects_process_env_or_fallback(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(_ctx(tmp_path / "config.ts", ["const retries = process.env.RETRIES || 0;"]))
    assert len(findings) == 1
    assert "logical-or primitive fallback" in findings[0].message


def test_detects_process_env_nullish_fallback(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(
        _ctx(tmp_path / "config.ts", ["const enabled = process.env.ENABLED ?? false;"])
    )
    assert len(findings) == 1
    assert "nullish primitive fallback" in findings[0].message


def test_no_finding_for_required_env_read(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(_ctx(tmp_path / "app.py", ['api_key = os.getenv("API_KEY")']))
    assert findings == []


def test_no_finding_for_non_primitive_purposeful_env_fallback(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(
        _ctx(tmp_path / "config.ts", ['const api = process.env.API_URL || "http://localhost";'])
    )
    assert findings == []


def test_detects_python_catch_all_returns_primitive(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(_ctx(tmp_path / "svc.py", ["except Exception: return []"]))
    assert len(findings) == 1
    assert "catch-all returns primitive" in findings[0].message


def test_detects_js_catch_all_returns_primitive(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    findings = rule.run(_ctx(tmp_path / "svc.ts", ["catch (e) { return null; }"]))
    assert len(findings) == 1
    assert "catch-all returns primitive" in findings[0].message


def test_pragma_rule_specific_suppresses(tmp_path: Path) -> None:
    rule = FallbackDefaultsRule()
    line = 'timeout = os.getenv("TIMEOUT", 0)  # slopsniff: ignore fallback-defaults'
    assert rule.run(_ctx(tmp_path / "settings.py", [line])) == []
