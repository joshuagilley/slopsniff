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

---

## Language support

| Language   | Parser              | Function detection                                    |
| ---------- | ------------------- | ----------------------------------------------------- |
| Python     | `ast` module        | Full — accurate line spans, nested functions          |
| JavaScript | Regex + brace depth | Heuristic — `function`, arrow functions, `const fn =` |
| TypeScript | Regex + brace depth | Same as JS                                            |
| TSX        | Regex + brace depth | Same as JS                                            |
| Vue        | Regex + brace depth | Same as JS                                            |

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
                          └── HelperSprawlRule (filename check)
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
│           └── helper_sprawl.py
└── tests/
    ├── test_walker.py
    ├── test_large_file.py
    ├── test_large_function.py
    ├── test_duplicate_functions.py
    └── test_helper_sprawl.py
```

---

## CI/CD integration

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

## Defaults reference

| Setting                      | Default                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Max file lines (warning)     | 400                                                                           |
| Max file lines (high)        | 800                                                                           |
| Max function lines (warning) | 50                                                                            |
| Max function lines (high)    | 100                                                                           |
| Fail threshold               | 20                                                                            |
| Included extensions          | `.py` `.js` `.ts` `.tsx` `.vue`                                               |
| Excluded directories         | `.git` `node_modules` `.nuxt` `dist` `build` `.venv` `coverage` `__pycache__` |

---

## Why I built this

AI has changed how code gets written. Not just for junior developers or people learning on the job — for everyone. Senior engineers who know exactly what good code looks like are shipping more of it faster than ever, and some of it is getting into main before anyone has had a chance to really look at it.

That's not a failure of discipline. It's a workflow problem. When you can generate a working function in thirty seconds, the refine-and-consolidate pass that used to happen naturally during the writing process gets skipped. You end up with code that works, passes a review, maybe even passes your tests — but quietly adds weight to the codebase. A utility file that should have been three focused modules. A function that does six things. The same transformation logic implemented twice because nobody noticed it already existed in a helper somewhere.

This compounds. One file at 600 lines is fine. Ten files at 600 lines, all named some variation of `utils` or `helpers`, with overlapping responsibilities and no clear owner — that's how a codebase becomes expensive to work in. Nobody planned it. It accumulated.

SlopSniff is a lightweight smoke alarm for that kind of drift. It runs in CI, scores the findings, and fails the build when the slop score crosses a threshold you control. It does not replace a real code review. It does not catch everything. But it does create a feedback loop early enough in the pipeline to matter — before the pattern hardens, before the duplication spreads, before the next person has to navigate a file they did not write and cannot easily reason about.

The rules in the first version are simple by design: large files, large functions, duplicate function bodies, and helper sprawl. Deterministic, explainable, fast. The goal was not to build something clever. The goal was to build something that teams would actually leave running.

## Roadmap

- [ ] `.slopsniff.toml` config file support
- [ ] `--changed-only` mode via `git diff`
- [ ] Near-duplicate detection (token fingerprints / MinHash)
- [ ] Tree-sitter integration for accurate multi-language AST
- [ ] GitHub PR annotation support
- [ ] Score baselining for legacy repos
- [ ] Suppression comments (`# slopsniff: ignore`)
- [ ] Homebrew tap
