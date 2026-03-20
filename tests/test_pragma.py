from slopsniff.pragma import line_ignores_rule


def test_global_ignore_no_rule_list() -> None:
    assert line_ignores_rule("x = 1  # slopsniff: ignore", "exposed-secrets") is True
    assert line_ignores_rule("// slopsniff: ignore", "exposed-secrets") is True


def test_rule_specific_ignore() -> None:
    line = "token  # slopsniff: ignore exposed-secrets"
    assert line_ignores_rule(line, "exposed-secrets") is True
    assert line_ignores_rule(line, "large-file") is False


def test_multiple_rules_in_pragma() -> None:
    line = "x  # slopsniff: ignore large-file, exposed-secrets"
    assert line_ignores_rule(line, "exposed-secrets") is True
    assert line_ignores_rule(line, "large-file") is True
    assert line_ignores_rule(line, "duplicate-functions") is False


def test_case_insensitive() -> None:
    assert line_ignores_rule("# SlopSniff: IGNORE exposed-secrets", "exposed-secrets") is True


def test_no_pragma() -> None:
    assert line_ignores_rule("AWS_ACCESS_KEY_ID=foo", "exposed-secrets") is False
