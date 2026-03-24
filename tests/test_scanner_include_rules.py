from slopsniff.config import Config
from slopsniff.scanner import scan


def test_without_config_or_include_runs_all_rules(tmp_path) -> None:
    # No slopsniff.json present, and Config.include_rules defaults to None.
    # This line should trigger fallback-defaults under default behavior.
    (tmp_path / "app.py").write_text('timeout = os.getenv("TIMEOUT", 0)\n')

    result = scan(tmp_path, Config())

    assert any(f.rule_id == "fallback-defaults" for f in result.findings)


def test_include_rules_filters_findings(tmp_path) -> None:
    # Would trigger both fallback-defaults and exposed-secrets.
    (tmp_path / "app.py").write_text(
        'api_key = "ghp_' + ("a" * 36) + '"\ntimeout = os.getenv("TIMEOUT", 0)\n'
    )

    config = Config(include_rules=["fallback-defaults"])
    result = scan(tmp_path, config)

    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "fallback-defaults"


def test_include_rules_unknown_rule_raises(tmp_path) -> None:
    (tmp_path / "app.py").write_text('timeout = os.getenv("TIMEOUT", 0)\n')
    config = Config(include_rules=["does-not-exist"])

    try:
        scan(tmp_path, config)
        assert False, "Expected scan to raise ValueError for unknown include rule"
    except ValueError as exc:
        assert "Unknown rule id" in str(exc)
