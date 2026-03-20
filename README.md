# SlopSniff

<p align="center">
  <img src="assets/logo.png" alt="SlopSniff" width="320" />
</p>

<p align="center">
  <a href="https://pypi.org/project/slopsniff/"><img src="https://img.shields.io/pypi/v/slopsniff.svg" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/slopsniff/"><img src="https://img.shields.io/pypi/pyversions/slopsniff.svg" alt="Python versions" /></a>
  <a href="https://github.com/joshuagilley/slopsniff/actions/workflows/ci.yml"><img src="https://github.com/joshuagilley/slopsniff/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/slopsniff/"><img src="https://img.shields.io/pypi/dm/slopsniff.svg" alt="Monthly downloads" /></a>
</p>

<p align="center">
  <strong><a href="https://pypi.org/project/slopsniff/">pypi.org/project/slopsniff</a></strong>
</p>

A lightweight CLI for catching "slop" in modern codebases before it hardens into team-wide tech debt.

SlopSniff is not trying to detect whether code was written by AI. It is trying to detect the kinds of patterns that show up when teams move too fast, overgenerate code, or skip the cleanup pass — giant files, copy-pasted functions, versioned helper sprawl, and everything else that quietly becomes the norm.

---

## Install

```bash
pip install slopsniff
```

Or with `uv`:

```bash
uv add slopsniff
```

---

## Usage

```bash
# Scan current directory
slopsniff .

# Scan a specific path
slopsniff ./src

# Set a custom CI fail threshold (default: 20)
slopsniff . --fail-threshold 30

# JSON output for machines and CI pipelines
slopsniff . --format json

# Show score contribution per finding
slopsniff . --verbose

# Override thresholds on the fly
slopsniff . --max-file-lines 300 --max-function-lines 40
```

### All flags

| Flag                   | Short | Default    | Description                              |
| ---------------------- | ----- | ---------- | ---------------------------------------- |
| `path`                 |       | `.`        | Directory to scan                        |
| `--fail-threshold`     | `-t`  | `20`       | Score at which CI returns exit code 1    |
| `--format`             | `-f`  | `terminal` | Output format: `terminal` or `json`      |
| `--verbose`            | `-v`  | off        | Show score per finding                   |
| `--max-file-lines`     |       | `400`      | Override file line warning threshold     |
| `--max-function-lines` |       | `50`       | Override function line warning threshold |

---

## Example output

```
SlopSniff Report
========================================
Files scanned:  42
Total score:    18
Status:         WARNING

[HIGH] duplicate-functions
  src/utils/formatters.py:12-44
  Duplicate function body found in 2 locations: src/utils/formatters.py:12-44, src/services/formatters.py:8-40

[MEDIUM] large-function
  src/api/upload.py:77-156
  Function 'process_upload' is 79 lines long (warning threshold: 50)

[LOW] large-file
  src/helpers/common.py
  File is 438 lines long (warning threshold: 400)
```

---

## Scoring

Each finding contributes to a total slop score.

| Severity | Score |
| -------- | ----- |
| high     | 10    |
| medium   | 5     |
| low      | 2     |

| Score range | Status               |
| ----------- | -------------------- |
| 0–9         | healthy              |
| 10–19       | warning              |
| 20+         | fail (non-zero exit) |

The fail threshold is configurable via `--fail-threshold`.

---

## Rules

### `large-file`

Flags files that exceed configurable line count thresholds.

- **medium** at 400+ lines
- **high** at 800+ lines

### `large-function`

Flags functions that exceed configurable line count thresholds. Uses Python's `ast` module for accurate line spans in `.py` files, and brace-depth heuristics for JS/TS/Vue.

- **medium** at 50+ lines
- **high** at 100+ lines

### `duplicate-functions`

Normalizes and hashes function bodies, then flags exact duplicates found across or within files. Functions under 5 lines are ignored to reduce noise from trivial patterns like empty `__init__` methods.

- **high** for any exact body match across 2+ locations

### `helper-sprawl`

Flags two categories of low-cohesion patterns:

1. **Generic filenames** — files named `utils.py`, `helpers.py`, `common.py`, `shared.py`, `misc.py`, etc.
2. **Versioned function names** — clusters of functions sharing a base name with variant suffixes like `_v2`, `_old`, `_safe`, `_legacy`, `_copy`, `_temp`

- **low** for generic filenames
- **medium** for versioned function name clusters

### `exposed-secrets`

Line-based heuristics for strings that **look like real credentials** (PEM private key headers, AWS key IDs, GitHub PATs, Slack/Stripe/OpenAI/Anthropic/Google/SendGrid-style tokens). Intended to catch accidents like pasting env vars into a blog post, component, or markdown file—not to prove a string is a live secret.

- **high** for any line matching one of the built-in patterns (rotate the credential even if it was “just for a screenshot”)

---

## Language support

| Language   | Parser              | Function detection                                    |
| ---------- | ------------------- | ----------------------------------------------------- |
| Python     | `ast` module        | Full — accurate line spans, nested functions          |
| JavaScript | Regex + brace depth | Heuristic — `function`, arrow functions, `const fn =` |
| TypeScript | Regex + brace depth | Same as JS                                            |
| TSX        | Regex + brace depth | Same as JS                                            |
| JSX        | Regex + brace depth | Same as JS                                            |
| Vue        | Regex + brace depth | Same as JS                                            |
| Markdown   | —                   | No function rules; `exposed-secrets` scans lines      |
| MDX        | —                   | Same as Markdown                                      |
| HTML       | —                   | Same as Markdown                                      |

---

## Architecture

```
Walk repo
  └── Filter by extension, skip excluded dirs
        └── Parse each file into FileContext
              ├── python_ast.py  →  ast.FunctionDef extraction
              └── text_parser.py →  regex + brace-depth heuristics
                    └── Run per-file rules
                          ├── LargeFileRule
                          ├── LargeFunctionRule
                          ├── HelperSprawlRule (filename check)
                          └── ExposedSecretsRule (line regexes)
                    └── Run cross-file rules (after all files parsed)
                          ├── DuplicateFunctionsRule (hash map)
                          └── HelperSprawlRule (versioned name clusters)
                                └── Aggregate findings
                                      └── Compute score → ScanResult
                                            └── Reporter (terminal | json)
                                                  └── Exit 0 or 1
```

### Data model

```python
@dataclass
class Finding:
    rule_id: str
    severity: str        # "low" | "medium" | "high"
    file_path: str
    line_start: int | None
    line_end: int | None
    message: str
    score: int

@dataclass
class ScanResult:
    findings: list[Finding]
    total_score: int
    files_scanned: int
    passed: bool
```

### Rule interface

Each per-file rule implements:

```python
def run(self, file_context: FileContext) -> list[Finding]: ...
```

Each cross-file rule implements:

```python
def run_cross_file(self, contexts: list[FileContext]) -> list[Finding]: ...
```

Rules are plain classes — no magic, no registration, easy to test in isolation.

---

## File structure

```
slopsniff/
├── pyproject.toml
├── README.md
├── src/
│   └── slopsniff/
│       ├── __init__.py
│       ├── cli.py          # Typer entrypoint
│       ├── config.py       # Config dataclass and defaults
│       ├── models.py       # Finding, FunctionInfo, FileContext, ScanResult
│       ├── scanner.py      # Scan pipeline orchestration
│       ├── scoring.py      # compute_score(), grade()
│       ├── walker.py       # Repo traversal with filtering
│       ├── parsers/
│       │   ├── python_ast.py   # ast-based Python parser
│       │   └── text_parser.py  # Regex/brace parser for JS/TS/Vue
│       ├── reporters/
│       │   ├── terminal.py     # Colored terminal output
│       │   └── json_reporter.py
│       └── rules/
│           ├── base.py                  # PerFileRule / CrossFileRule protocols
│           ├── large_file.py
│           ├── large_function.py
│           ├── duplicate_functions.py
│           ├── exposed_secrets.py
│           └── helper_sprawl.py
└── tests/
    ├── test_walker.py
    ├── test_large_file.py
    ├── test_large_function.py
    ├── test_duplicate_functions.py
    ├── test_exposed_secrets.py
    └── test_helper_sprawl.py
```

---

## Using SlopSniff in CI

### GitHub Actions

```yaml
name: SlopSniff

on:
  pull_request:
  push:
    branches: [main]

jobs:
  slopsniff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install SlopSniff
        run: pip install slopsniff

      - name: Run SlopSniff
        run: slopsniff . --fail-threshold 20
```

SlopSniff returns exit code `1` when the total score meets or exceeds the threshold, making it a drop-in CI gate.

---

## Development

```bash
# Clone and install with dev deps
git clone https://github.com/joshuagilley/slopsniff
cd slopsniff
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Run CLI locally
uv run slopsniff .
```

---

## Release to PyPI

Publishing is automated in [`.github/workflows/publish.yml`](.github/workflows/publish.yml): when a **GitHub Release is published**, Actions builds with `uv build` and uploads to PyPI via trusted publishing (OIDC). Pushing a tag by itself does not run the publish job—you must **publish** a GitHub Release for that tag.

1. **Feature branch** — Branch from `main`, ship changes via PR, merge when CI passes.
2. **Sync `main`** — `git checkout main && git pull`.
3. **Version** — Bump `[project].version` in `pyproject.toml` (that value is what PyPI shows). Commit and push to `main` (e.g. `chore: release 0.1.6`).
4. **Tag + GitHub Release** — Tag `v` + semver to match `pyproject.toml` (e.g. `v0.1.6` for `0.1.6`), push the tag, then create and **Publish** a GitHub Release on that tag (UI: Releases → Draft → pick tag → Publish).

   With [GitHub CLI](https://cli.github.com/):

   ```bash
   git tag v0.1.6
   git push origin v0.1.6
   gh release create v0.1.6 --title "0.1.6" --notes "Brief summary of changes."
   ```

Configure [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) for this repo (and the `release` environment in GitHub if you use approval rules).

**If publish fails with `HTTPError: 400 Bad Request`:** PyPI rejects uploading a **filename that already exists** (wheel and sdist names include the version). That almost always means **that version is already on PyPI**.

**Re-running a release never picks up `main`.** “Re-run all jobs” on an old tag checks out that tag again, so `uv build` keeps producing the same filenames and PyPI may reject duplicates. **Fix:** merge your bumped `pyproject.toml` on `main`, create a **new** tag (e.g. **`v0.1.6`**) on that commit, push it, then **create a new GitHub Release** for that tag and publish it. Do not re-run the old release workflow when you need a new version. Deleting a GitHub Release does not remove files from PyPI.

---

## Defaults reference

| Setting                      | Default                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Max file lines (warning)     | 400                                                                           |
| Max file lines (high)        | 800                                                                           |
| Max function lines (warning) | 50                                                                            |
| Max function lines (high)    | 100                                                                           |
| Fail threshold               | 20                                                                            |
| Included extensions          | `.py` `.js` `.ts` `.tsx` `.jsx` `.vue` `.md` `.mdx` `.html`                   |
| Excluded directories         | `.git` `node_modules` `.nuxt` `dist` `build` `.venv` `coverage` `__pycache__` |

---

## Roadmap

- [ ] `.slopsniff.toml` config file support
- [ ] `--changed-only` mode via `git diff`
- [ ] Near-duplicate detection (token fingerprints / MinHash)
- [ ] Tree-sitter integration for accurate multi-language AST
- [ ] GitHub PR annotation support
- [ ] Score baselining for legacy repos
- [ ] Suppression comments (`# slopsniff: ignore`)
- [ ] Homebrew tap
