"""Resolve files changed vs a git ref (same idea as ``git diff <ref> --name-only``)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config import Config
from .walker import path_matches_scan


def _run_git(repo_root: Path, *args: str) -> str:
    cmd = ["git", "-C", str(repo_root), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip() or f"exit {result.returncode}"
        raise ValueError(f"git failed ({' '.join(cmd)}): {err}")
    return result.stdout


def git_repo_root(start: Path) -> Path:
    """Return the git work tree root containing ``start``."""
    start = start.resolve()
    if start.is_file():
        start = start.parent
    out = _run_git(start, "rev-parse", "--show-toplevel").strip()
    if not out:
        raise ValueError("git rev-parse --show-toplevel returned empty output")
    return Path(out).resolve()


def git_changed_paths(repo_root: Path, ref: str) -> list[str]:
    """Paths relative to repo root (POSIX), added/copied/modified/renamed vs current tree."""
    stdout = _run_git(
        repo_root,
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        ref,
        "--",
    )
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def scan_paths_from_git_diff(scan_root: Path, config: Config, ref: str) -> list[Path]:
    """Files under ``scan_root`` that are included by config and changed vs ``ref``."""
    scan_root = scan_root.resolve()
    repo_root = git_repo_root(scan_root)
    rel_lines = git_changed_paths(repo_root, ref)
    seen: set[Path] = set()
    out: list[Path] = []
    for rel in rel_lines:
        candidate = (repo_root / rel).resolve()
        if candidate in seen:
            continue
        if not path_matches_scan(scan_root, candidate, config):
            continue
        seen.add(candidate)
        out.append(candidate)
    return sorted(out)
