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

## Quick Start

<table>
<tr>
<th>JavaScript / TypeScript (app repo)</th>
<th>Python (app repo)</th>
</tr>
<tr>
<td>

```bash
# One-off run
npx slopsniff-cli .

# or install locally
npm i -D slopsniff-cli
```

```json
{
  "scripts": {
    "slopsniff": "slopsniff .",
    "slopsniff:strict": "slopsniff . --fail-threshold 0 --format json"
  }
}
```

</td>
<td>

```bash
# install in your Python project
uv add --dev slopsniff
# or: pip install slopsniff
```

```bash
# run in your project
slopsniff .
# optional strict mode
slopsniff . --fail-threshold 0 --format json
```

</td>
</tr>
</table>

Notes:

- The npm package is a wrapper around the Python CLI.
- It runs `slopsniff` via `uv tool run --from slopsniff ...`.
- On macOS/Linux, it will attempt to install `uv` automatically if missing.
- Commit a `slopsniff.json` in your project root to configure rules and exclusions.

---

### What it catches

<table>
<tr>
<th>Pattern</th>
<th>Slop</th>
<th>Better</th>
</tr>

<tr>
<td><strong>Fallback defaults</strong><br><sub>Silent primitives that mask missing config</sub></td>
<td>

```python
timeout = os.getenv("TIMEOUT", 0)
```

```js
const retries = process.env.RETRIES || 0;
```

</td>
<td>

```python
timeout = require_env("TIMEOUT")
```

```js
const retries = requireEnv("RETRIES");
```

</td>
</tr>

<tr>
<td><strong>Catch-all primitive returns</strong><br><sub>Flattens every failure into one silent shape</sub></td>
<td>

```python
except Exception:
    return []
```

```js
catch (e) { return null; }
```

</td>
<td>

```python
except TimeoutError:
    logger.warning("upstream timeout")
    raise
```

```js
catch (e) {
  if (e instanceof RateLimitError) { ... }
  throw e;
}
```

</td>
</tr>

<tr>
<td><strong>Exposed secrets</strong><br><sub>Credentials committed in source or docs</sub></td>
<td>

```python
API_KEY = "sk-proj-abc123..."
```

</td>
<td>

```python
API_KEY = os.environ["API_KEY"]
```

</td>
</tr>

<tr>
<td><strong>Large files &amp; functions</strong><br><sub>Monoliths that resist review and testing</sub></td>
<td>

```
scanner.py — 800+ lines
def do_everything(): — 120 lines
```

</td>
<td>

```
scanner.py — focused orchestrator
def scan(): — delegates to helpers
```

</td>
</tr>

<tr>
<td><strong>Duplicate functions</strong><br><sub>Copy-pasted logic across files</sub></td>
<td>

```
utils.py:  def format_date(d): ...
helpers.py: def format_date(d): ...  # identical
```

</td>
<td>

```
dates.py: def format_date(d): ...  # single source
```

</td>
</tr>

<tr>
<td><strong>Helper sprawl</strong><br><sub>Vague catch-all files and versioned copies</sub></td>
<td>

```
utils.py, helpers.py, common.py
send_email_v2(), format_data_old()
```

</td>
<td>

```
email_service.py, formatters.py
send_email(), format_data()
```

</td>
</tr>
</table>

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
env PYTHONPATH=src uv run python -m slopsniff.cli . --fail-threshold 30
```

Notes:

- Pre-commit runs `ruff`, `ruff-format`, `slopsniff`, and `pytest`.
- Terminal output uses [Rich](https://github.com/textualize/rich). Use `--format json` for machine output.
- For local runs, prefer `env PYTHONPATH=src uv run python -m slopsniff.cli ...`.

---

## Basic Usage

```bash
# Scan current directory
env PYTHONPATH=src uv run python -m slopsniff.cli .

# Scan a specific path
env PYTHONPATH=src uv run python -m slopsniff.cli ./src

# JSON output for CI/machines
env PYTHONPATH=src uv run python -m slopsniff.cli . --format json

# Override thresholds ad hoc
env PYTHONPATH=src uv run python -m slopsniff.cli . --max-file-lines 300 --max-function-lines 40
```

---

## Configuration (`slopsniff.json`)

SlopSniff auto-loads `slopsniff.json` from the scan root (the path you pass to `slopsniff`).
You can tune scoring thresholds, file selection, and enabled rules in one place.

Example:

```json
{
  "fail-threshold": 20,
  "max-file-lines-warning": 400,
  "max-file-lines-high": 800,
  "max-function-lines-warning": 50,
  "max-function-lines-high": 100,
  "verbose": false,
  "include-extensions": [".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".html"],
  "large-file-extensions": [".py", ".js", ".ts", ".tsx", ".jsx", ".vue"],
  "exclude-files": ["temp_slop_examples.py", "src/fixtures/example.py"],
  "exclude-dirs": [".git", "node_modules", ".venv", "tests", "dist", "build"],
  "include": [
    "fallback-defaults",
    "exposed-secrets",
    "large-function",
    "large-file",
    "duplicate-functions",
    "helper-sprawl"
  ]
}
```

Rule IDs for `include`:

- `fallback-defaults`
- `exposed-secrets`
- `large-function`
- `large-file`
- `duplicate-functions`
- `helper-sprawl`

Notes:

- CLI flags still work and override file values (for example, `--fail-threshold`).
- If `include` is omitted, all rules run.
- `exclude-files` accepts either bare filenames or scan-root-relative paths.
- Unknown keys and unknown rule IDs fail fast with clear errors.

---

## Contributing and Commits

Standard flow:

1. Create a feature branch from `main`.
2. Make changes.
3. Run checks locally:
   ```bash
   uv run pytest
   uv run ruff check .
   env PYTHONPATH=src uv run python -m slopsniff.cli . --fail-threshold 30
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
