from pathlib import Path

from slopsniff.models import FileContext, FunctionInfo
from slopsniff.rules.duplicate_functions import DuplicateFunctionsRule


def _ctx(path: Path, functions: list[FunctionInfo]) -> FileContext:
    return FileContext(path=path, lines=[], language="python", functions=functions)


def _fn(name: str, path: str, start: int, end: int, body_hash: str) -> FunctionInfo:
    return FunctionInfo(name=name, file_path=path, line_start=start, line_end=end, body_hash=body_hash)


def test_no_finding_for_unique_functions(tmp_path: Path) -> None:
    rule = DuplicateFunctionsRule()
    ctx_a = _ctx(tmp_path / "a.py", [_fn("fn_a", "a.py", 1, 20, "hash_a")])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("fn_b", "b.py", 1, 20, "hash_b")])
    assert rule.run_cross_file([ctx_a, ctx_b]) == []


def test_finding_for_duplicate_hash_across_files(tmp_path: Path) -> None:
    rule = DuplicateFunctionsRule()
    shared = "deadbeef1234"
    ctx_a = _ctx(tmp_path / "a.py", [_fn("fn_a", "a.py", 1, 20, shared)])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("fn_b", "b.py", 1, 20, shared)])
    findings = rule.run_cross_file([ctx_a, ctx_b])
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].rule_id == "duplicate-functions"


def test_finding_for_duplicate_hash_within_file(tmp_path: Path) -> None:
    rule = DuplicateFunctionsRule()
    shared = "cafebabe5678"
    ctx = _ctx(
        tmp_path / "a.py",
        [
            _fn("fn_a", "a.py", 1, 20, shared),
            _fn("fn_b", "a.py", 30, 50, shared),
        ],
    )
    findings = rule.run_cross_file([ctx])
    assert len(findings) == 1


def test_short_functions_are_ignored(tmp_path: Path) -> None:
    """Functions under _MIN_LINES should not trigger duplicate detection."""
    rule = DuplicateFunctionsRule()
    shared = "tiny_hash"
    ctx_a = _ctx(tmp_path / "a.py", [_fn("fn_a", "a.py", 1, 3, shared)])
    ctx_b = _ctx(tmp_path / "b.py", [_fn("fn_b", "b.py", 1, 3, shared)])
    assert rule.run_cross_file([ctx_a, ctx_b]) == []


def test_three_way_duplicate(tmp_path: Path) -> None:
    rule = DuplicateFunctionsRule()
    shared = "triple_hash"
    contexts = [
        _ctx(tmp_path / f"{name}.py", [_fn(name, f"{name}.py", 1, 25, shared)])
        for name in ["a", "b", "c"]
    ]
    findings = rule.run_cross_file(contexts)
    assert len(findings) == 1
    assert "3 locations" in findings[0].message
