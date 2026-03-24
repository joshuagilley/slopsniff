import json

import pytest

from slopsniff.config import load_include_rules


def test_load_include_rules_from_json(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(
        json.dumps({"include": ["fallback-defaults", "exposed-secrets"]})
    )
    include = load_include_rules(tmp_path)
    assert include == ["fallback-defaults", "exposed-secrets"]


def test_load_include_rules_returns_none_when_missing(tmp_path) -> None:
    assert load_include_rules(tmp_path) is None


def test_load_include_rules_invalid_json_shape(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(json.dumps({"include": "fallback-defaults"}))
    with pytest.raises(ValueError, match="include"):
        load_include_rules(tmp_path)
