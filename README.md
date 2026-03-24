# SlopSniff

<p align="center">
  <img src="assets/logo.png" alt="SlopSniff" width="320" />
</p>

<p align="center">
  <a href="https://pypi.org/project/slopsniff/"><img src="https://img.shields.io/pypi/v/slopsniff.svg" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/slopsniff/"><img src="https://img.shields.io/pypi/pyversions/slopsniff.svg" alt="Python versions" /></a>
  <a href="https://github.com/joshuagilley/slopsniff/actions/workflows/ci.yml"><img src="https://github.com/joshuagilley/slopsniff/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
</p>

A lightweight CLI for catching code-quality drift ("slop") before it hardens into team-wide tech debt.

---

## Local Setup (Open Source Dev)

```bash
git clone https://github.com/joshuagilley/slopsniff
cd slopsniff
uv sync --dev
pre-commit install
```

Quick sanity run:

```bash
uv run pytest
uv run ruff check .
uv run slopsniff . --fail-threshold 30
```

Notes:
- Pre-commit runs `ruff`, `ruff-format`, `slopsniff`, and `pytest`.
- Terminal output uses [Rich](https://github.com/textualize/rich). Use `--format json` for machine output.

---

## Basic Usage

```bash
# Scan current directory
uv run slopsniff .

# Scan a specific path
uv run slopsniff ./src

# JSON output for CI/machines
uv run slopsniff . --format json

# Override thresholds ad hoc
uv run slopsniff . --max-file-lines 300 --max-function-lines 40
```

---

## Configuration (`slopsniff.json`)

SlopSniff auto-loads `slopsniff.json` from the scan root (the path you pass to `slopsniff`).
Use `include` to restrict checks to only the rule IDs your team cares about.

Example:

```json
{
  "include": [
    "fallback-defaults",
    "exposed-secrets",
    "large-function"
  ]
}
```

Available rule IDs:
- `fallback-defaults`
- `exposed-secrets`
- `large-function`
- `large-file`
- `duplicate-functions`
- `helper-sprawl`

Notes:
- If `include` is omitted, all rules run.
- Unknown rule IDs fail fast with a clear error so CI config mistakes are visible.

---

## Contributing and Commits

Standard flow:

1. Create a feature branch from `main`.
2. Make changes.
3. Run checks locally:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run slopsniff . --fail-threshold 30
   ```
4. Commit with a clear message.
5. Open a PR and merge after CI passes.

---

## Release Process

Publishing is handled by [`.github/workflows/publish.yml`](.github/workflows/publish.yml).
It runs on **GitHub Release published** (not on tag push alone).

### Recommended: one-command release script

From repo root, on `main`, with a clean working tree:

```bash
./scripts/release.py 0.1.9
# or:
uv run python scripts/release.py v0.1.9
```

What it does:
1. Pulls `main`.
2. Bumps version in `pyproject.toml` and `src/slopsniff/__init__.py`.
3. Runs `uv lock`.
4. Commits `chore: release X.Y.Z`.
5. Pushes `main`.
6. Tags `vX.Y.Z` and pushes the tag.
7. Creates/publishes a GitHub release with `gh release create`.

Useful flags:
- `--dry-run`
- `--no-pull`
- `--allow-dirty`
- `--notes-file PATH`
- `--expect-repo OWNER/REPO`

Optional guard:
- Set `SLOPSNIFF_RELEASE_EXPECT_REPO=joshuagilley/slopsniff` to prevent accidental release from a fork clone.

### If release/publish fails

- **`HTTP 400` from PyPI:** that version already exists; bump to a new version and release again.
- **`HTTP 422` from `gh release create`:** release already exists for that tag. Re-run workflow for that release if needed.
- Re-running old releases uses the same tagged commit; it does not pick up newer `main`.

---

## Minimal Architecture Notes

Pipeline:
1. Walk repo and collect included files.
2. Parse functions (`ast` for Python, heuristic parser for JS/TS/TSX/JSX/Vue).
3. Run per-file rules.
4. Run cross-file rules.
5. Aggregate findings and score.
6. Report (`terminal` via Rich or `json`) and exit non-zero on threshold fail.

Key paths:
- `src/slopsniff/cli.py` — CLI entrypoint
- `src/slopsniff/scanner.py` — orchestration
- `src/slopsniff/rules/` — rule implementations
- `src/slopsniff/reporters/` — terminal/json output
- `scripts/release.py` — scripted release flow
