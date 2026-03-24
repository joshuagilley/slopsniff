from pathlib import Path

import pytest

from slopsniff import git_scope
from slopsniff.config import Config
from slopsniff.scanner import scan


def test_git_repo_root_requires_git(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="git"):
        git_scope.git_repo_root(tmp_path)


def test_scan_paths_from_git_diff_lists_modified_tracked_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    (root / "tracked.py").write_text("x = 1\n")

    def fake_run_git(repo: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return f"{root}\n"
        if args[:4] == ("diff", "--name-only", "--diff-filter=ACMR", "main"):
            return "tracked.py\n"
        raise AssertionError(args)

    monkeypatch.setattr(git_scope, "_run_git", fake_run_git)
    config = Config()
    paths = git_scope.scan_paths_from_git_diff(tmp_path, config, "main")
    assert paths == [root / "tracked.py"]


def test_scan_paths_from_git_diff_respects_scan_subdirectory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    pkg = root / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text("a = 1\n")

    def fake_run_git(repo: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return f"{root}\n"
        if args[:4] == ("diff", "--name-only", "--diff-filter=ACMR", "main"):
            return "pkg/mod.py\n"
        raise AssertionError(args)

    monkeypatch.setattr(git_scope, "_run_git", fake_run_git)
    config = Config()
    paths = git_scope.scan_paths_from_git_diff(pkg, config, "main")
    assert paths == [pkg / "mod.py"]


def test_scan_paths_from_git_diff_empty_when_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    (root / "tracked.py").write_text("x = 1\n")

    def fake_run_git(repo: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return f"{root}\n"
        if args[:4] == ("diff", "--name-only", "--diff-filter=ACMR", "main"):
            return ""
        raise AssertionError(args)

    monkeypatch.setattr(git_scope, "_run_git", fake_run_git)
    config = Config()
    assert git_scope.scan_paths_from_git_diff(tmp_path, config, "main") == []


def test_scan_changed_since_runs_on_git_subset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    (root / "tracked.py").write_text(
        'import os\ntimeout = os.getenv("TIMEOUT", 0)\n',
    )
    (root / "dirty.py").write_text(
        'import os\ntimeout = os.getenv("OTHER", 0)\n',
    )

    def fake_run_git(repo: Path, *args: str) -> str:
        if args == ("rev-parse", "--show-toplevel"):
            return f"{root}\n"
        if args[:4] == ("diff", "--name-only", "--diff-filter=ACMR", "main"):
            return "tracked.py\n"
        raise AssertionError(args)

    monkeypatch.setattr(git_scope, "_run_git", fake_run_git)
    config = Config()
    result = scan(tmp_path, config, changed_since="main")
    assert result.files_scanned == 1
    assert result.findings
    assert all("dirty.py" not in f.file_path for f in result.findings)
    assert any("tracked.py" in f.file_path for f in result.findings)
