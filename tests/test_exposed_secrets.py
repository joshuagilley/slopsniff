from pathlib import Path

from slopsniff.models import FileContext
from slopsniff.rules.exposed_secrets import ExposedSecretsRule


def _ctx(path: Path, lines: list[str]) -> FileContext:
    return FileContext(path=path, lines=lines, language="text")


def test_detects_aws_access_key_id(tmp_path: Path) -> None:
    key = "AKIA" + "0" * 16
    rule = ExposedSecretsRule()
    findings = rule.run(_ctx(tmp_path / "post.md", [f"AWS_ACCESS_KEY_ID={key}"]))
    assert len(findings) == 1
    assert findings[0].rule_id == "exposed-secrets"
    assert findings[0].severity == "high"
    assert findings[0].line_start == 1
    assert findings[0].score == 10
    assert "AWS access key id" in findings[0].message


def test_detects_github_classic_pat(tmp_path: Path) -> None:
    token = "ghp_" + "a" * 36
    rule = ExposedSecretsRule()
    findings = rule.run(_ctx(tmp_path / "leak.tsx", [f'const t = "{token}";']))
    assert len(findings) == 1
    assert "GitHub personal access token" in findings[0].message


def test_detects_pem_header(tmp_path: Path) -> None:
    rule = ExposedSecretsRule()
    pem = "-----BEGIN RSA PRIVATE KEY-----"  # slopsniff: ignore exposed-secrets
    findings = rule.run(_ctx(tmp_path / "x.py", [pem]))
    assert len(findings) == 1
    assert "PEM private key" in findings[0].message


def test_detects_stripe_secret(tmp_path: Path) -> None:
    rule = ExposedSecretsRule()
    findings = rule.run(_ctx(tmp_path / "env.html", ["sk_live_" + "x" * 24]))
    assert len(findings) == 1
    assert "Stripe" in findings[0].message


def test_clean_line_no_finding(tmp_path: Path) -> None:
    rule = ExposedSecretsRule()
    html = '<li class="blog-item" data-tags="architecture infrastructure">'
    assert rule.run(_ctx(tmp_path / "blog.html", [html])) == []


def test_multiple_patterns_one_line_single_finding(tmp_path: Path) -> None:
    """One finding per line; message lists all matched kinds."""
    aws = "AKIA" + "1" * 16
    ghp = "ghp_" + "b" * 36
    rule = ExposedSecretsRule()
    findings = rule.run(_ctx(tmp_path / "bad.md", [f"{aws} {ghp}"]))
    assert len(findings) == 1
    assert "AWS access key id" in findings[0].message
    assert "GitHub personal access token" in findings[0].message


def test_pragma_global_suppresses_line(tmp_path: Path) -> None:
    key = "AKIA" + "0" * 16
    rule = ExposedSecretsRule()
    line = f"KEY={key}  # slopsniff: ignore"
    assert rule.run(_ctx(tmp_path / "t.py", [line])) == []


def test_pragma_rule_specific_suppresses(tmp_path: Path) -> None:
    key = "AKIA" + "0" * 16
    rule = ExposedSecretsRule()
    line = f"KEY={key}  # slopsniff: ignore exposed-secrets"
    assert rule.run(_ctx(tmp_path / "t.py", [line])) == []


def test_edit_line_pragma_removed_finds_again(tmp_path: Path) -> None:
    """Changing the line (dropping pragma) surfaces the finding again."""
    key = "AKIA" + "0" * 16
    rule = ExposedSecretsRule()
    ignored = f"KEY={key}  # slopsniff: ignore"
    bare = f"KEY={key}"
    assert rule.run(_ctx(tmp_path / "a.py", [ignored])) == []
    assert len(rule.run(_ctx(tmp_path / "b.py", [bare]))) == 1
