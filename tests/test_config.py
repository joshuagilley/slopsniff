import json

import pytest

from slopsniff.config import load_config_overrides


def test_load_config_overrides_from_json(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(
        json.dumps(
            {
                "include": ["fallback-defaults", "exposed-secrets"],
                "fail-threshold": 12,
                "max-file-lines-warning": 320,
                "max-file-lines-high": 900,
                "max-function-lines-warning": 40,
                "max-function-lines-high": 120,
                "include-extensions": [".py", ".ts"],
                "exclude-dirs": [".git", "tests"],
                "exclude-files": ["temp_slop_examples.py", "src/fixtures/example.py"],
                "exclude-severities": ["low", "HIGH"],
                "verbose": True,
            }
        )
    )
    cfg = load_config_overrides(tmp_path)
    assert cfg is not None
    assert cfg["include"] == ["fallback-defaults", "exposed-secrets"]
    assert cfg["fail-threshold"] == 12
    assert cfg["max-file-lines-warning"] == 320
    assert cfg["max-file-lines-high"] == 900
    assert cfg["max-function-lines-warning"] == 40
    assert cfg["max-function-lines-high"] == 120
    assert cfg["include-extensions"] == [".py", ".ts"]
    assert cfg["exclude-dirs"] == [".git", "tests"]
    assert cfg["exclude-files"] == ["temp_slop_examples.py", "src/fixtures/example.py"]
    assert cfg["exclude-severities"] == ["low", "high"]
    assert cfg["verbose"] is True


def test_load_config_overrides_returns_none_when_missing(tmp_path) -> None:
    assert load_config_overrides(tmp_path) is None


def test_load_config_overrides_invalid_json_shape(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(json.dumps({"include": "fallback-defaults"}))
    with pytest.raises(ValueError, match="include"):
        load_config_overrides(tmp_path)


def test_load_config_overrides_rejects_unknown_key(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(json.dumps({"nope": 1}))
    with pytest.raises(ValueError, match="Unknown config key"):
        load_config_overrides(tmp_path)


def test_load_config_overrides_rejects_invalid_severity(tmp_path) -> None:
    (tmp_path / "slopsniff.json").write_text(json.dumps({"exclude-severities": ["critical"]}))
    with pytest.raises(ValueError, match="exclude-severities"):
        load_config_overrides(tmp_path)
