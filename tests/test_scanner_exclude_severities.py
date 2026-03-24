from slopsniff.config import Config
from slopsniff.scanner import scan


def test_exclude_severities_drops_matching_findings_and_score(tmp_path) -> None:
    (tmp_path / "app.py").write_text(
        'api_key = "ghp_' + ("a" * 36) + '"\ntimeout = os.getenv("TIMEOUT", 0)\n'
    )

    config = Config(exclude_severities=frozenset({"high"}))
    result = scan(tmp_path, config)

    assert all(f.severity != "high" for f in result.findings)
    assert any(f.rule_id == "fallback-defaults" for f in result.findings)
    assert not any(f.rule_id == "exposed-secrets" for f in result.findings)
    assert result.total_score == sum(f.score for f in result.findings)
