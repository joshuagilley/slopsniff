#!/usr/bin/env python3
"""Bump version, uv lock, commit, push main, tag, push tag, and publish a GitHub release.

Usage:
  ./scripts/release.py 0.1.7
  ./scripts/release.py v0.1.7
  ./scripts/release.py 0.1.7 --dry-run
  ./scripts/release.py 0.1.7 --no-pull
  ./scripts/release.py 0.1.7 --notes-file CHANGELOG-snippet.md

Requires: git, uv, gh (authenticated), clean working tree, branch main.

Optional safety: set SLOPSNIFF_RELEASE_EXPECT_REPO=owner/repo (or pass --expect-repo)
so the script refuses to run unless `gh repo view` matches (avoids releasing from a fork).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _ROOT / "pyproject.toml"
_INIT = _ROOT / "src" / "slopsniff" / "__init__.py"
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _run(cmd: list[str], *, dry_run: bool) -> None:
    print("+", " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, cwd=_ROOT, check=True)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str, *, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] would write {path.relative_to(_ROOT)}")
        return
    path.write_text(text, encoding="utf-8")


def _bump_pyproject(semver: str, *, dry_run: bool) -> None:
    text = _read_text(_PYPROJECT)
    new_text, n = re.subn(
        r'^version = "[^"]+"\s*$',
        f'version = "{semver}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n != 1:
        sys.exit("error: could not find a single version = line in pyproject.toml")
    _write_text(_PYPROJECT, new_text, dry_run=dry_run)


def _bump_init(semver: str, *, dry_run: bool) -> None:
    text = _read_text(_INIT)
    new_text, n = re.subn(
        r'^__version__ = "[^"]+"\s*$',
        f'__version__ = "{semver}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n != 1:
        sys.exit("error: could not find a single __version__ line in __init__.py")
    _write_text(_INIT, new_text, dry_run=dry_run)


def _git_porcelain() -> str:
    r = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def _current_branch() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def _gh_name_with_owner() -> str:
    r = subprocess.run(
        [
            "gh",
            "repo",
            "view",
            "--json",
            "nameWithOwner",
            "--jq",
            ".nameWithOwner",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        sys.exit(f"error: gh repo view failed: {err}")
    return r.stdout.strip()


def _assert_expected_repo(expected: str | None, *, dry_run: bool) -> None:
    if not expected:
        return
    exp = expected.strip()
    if dry_run:
        print(f"[dry-run] would require gh repo nameWithOwner == {exp!r}")
        return
    actual = _gh_name_with_owner()
    if actual.casefold() != exp.casefold():
        sys.exit(
            f"error: gh reports repo {actual!r}, expected {exp!r} "
            "(set SLOPSNIFF_RELEASE_EXPECT_REPO or use --expect-repo on the canonical clone)"
        )


def _commit_release(semver: str, *, dry_run: bool) -> None:
    cmd = ["git", "commit", "-m", f"chore: release {semver}"]
    print("+", " ".join(cmd))
    if dry_run:
        return

    first = subprocess.run(cmd, cwd=_ROOT)
    if first.returncode == 0:
        return

    # Common case: pre-commit formatter modified tracked files, so restage and retry once.
    if _git_porcelain():
        print("+ git add -u")
        subprocess.run(["git", "add", "-u"], cwd=_ROOT, check=True)
        print("+", " ".join(cmd))
        subprocess.run(cmd, cwd=_ROOT, check=True)
        return

    raise subprocess.CalledProcessError(first.returncode, cmd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SlopSniff release: version bump through gh release.",
    )
    parser.add_argument(
        "version",
        help='Semver, e.g. 0.1.7 or v0.1.7 (Git tag will be "v" + semver).',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands only; change nothing.",
    )
    parser.add_argument("--no-pull", action="store_true", help="Skip git pull origin main.")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow starting with a dirty working tree (unsafe).",
    )
    parser.add_argument(
        "--notes-file",
        metavar="PATH",
        help="Pass to gh release create as --notes-file (default: --generate-notes).",
    )
    parser.add_argument(
        "--expect-repo",
        metavar="OWNER/REPO",
        help=(
            "Abort unless `gh repo view` is this repo (e.g. joshuagilley/slopsniff). "
            "Default: env SLOPSNIFF_RELEASE_EXPECT_REPO."
        ),
    )
    args = parser.parse_args()

    raw = args.version.strip()
    semver = raw.removeprefix("v").removeprefix("V")
    if not _VERSION_RE.match(semver):
        sys.exit(f"error: expected semver like 0.1.7, got {args.version!r}")
    tag = f"v{semver}"

    dry = args.dry_run

    expect_repo = (
        args.expect_repo or os.environ.get("SLOPSNIFF_RELEASE_EXPECT_REPO") or ""
    ).strip() or None

    if not dry:
        if _current_branch() != "main":
            sys.exit("error: must be on branch main")
        dirty = _git_porcelain()
        if dirty and not args.allow_dirty:
            sys.exit("error: working tree is not clean (commit/stash first, or --allow-dirty)")
        _assert_expected_repo(expect_repo, dry_run=False)

    else:
        _assert_expected_repo(expect_repo, dry_run=True)

    if not args.no_pull:
        _run(["git", "pull", "origin", "main"], dry_run=dry)

    _bump_pyproject(semver, dry_run=dry)
    _bump_init(semver, dry_run=dry)
    _run(["uv", "lock"], dry_run=dry)

    paths = ["pyproject.toml", "uv.lock", "src/slopsniff/__init__.py"]
    _run(["git", "add", *paths], dry_run=dry)
    _commit_release(semver, dry_run=dry)
    _run(["git", "push", "origin", "main"], dry_run=dry)
    _run(["git", "tag", tag], dry_run=dry)
    _run(["git", "push", "origin", tag], dry_run=dry)

    gh_cmd = [
        "gh",
        "release",
        "create",
        tag,
        "--title",
        semver,
    ]
    if args.notes_file:
        gh_cmd.extend(["--notes-file", args.notes_file])
    else:
        gh_cmd.append("--generate-notes")
    _run(gh_cmd, dry_run=dry)

    if dry:
        print("\n(dry-run: no files or git remotes were changed)")
    else:
        print(f"\nDone. GitHub release for {tag} should trigger Publish to PyPI.")


if __name__ == "__main__":
    main()
