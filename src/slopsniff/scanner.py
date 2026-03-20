from pathlib import Path

from .config import Config
from .models import FileContext, Finding, ScanResult
from .parsers.python_ast import parse_python
from .parsers.text_parser import parse_text
from .rules.duplicate_functions import DuplicateFunctionsRule
from .rules.exposed_secrets import ExposedSecretsRule
from .rules.helper_sprawl import HelperSprawlRule
from .rules.large_file import LargeFileRule
from .rules.large_function import LargeFunctionRule
from .scoring import compute_score
from .walker import walk_repo


def _detect_language(path: Path) -> str:
    return "python" if path.suffix == ".py" else "text"


def _build_context(path: Path) -> FileContext | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    lines = text.splitlines()
    language = _detect_language(path)
    ctx = FileContext(path=path, lines=lines, language=language)
    ctx.functions = parse_python(path, lines) if language == "python" else parse_text(path, lines)
    return ctx


def scan(root: Path, config: Config) -> ScanResult:
    files = walk_repo(root, config)

    large_file_rule = LargeFileRule(config)
    large_fn_rule = LargeFunctionRule(config)
    duplicate_rule = DuplicateFunctionsRule()
    sprawl_rule = HelperSprawlRule()
    secrets_rule = ExposedSecretsRule()

    all_findings: list[Finding] = []
    contexts: list[FileContext] = []

    for file_path in files:
        ctx = _build_context(file_path)
        if ctx is None:
            continue
        contexts.append(ctx)
        all_findings.extend(large_file_rule.run(ctx))
        all_findings.extend(large_fn_rule.run(ctx))
        all_findings.extend(sprawl_rule.run(ctx))
        all_findings.extend(secrets_rule.run(ctx))

    all_findings.extend(duplicate_rule.run_cross_file(contexts))
    all_findings.extend(sprawl_rule.run_cross_file(contexts))

    total_score = compute_score(all_findings)
    return ScanResult(
        findings=all_findings,
        total_score=total_score,
        files_scanned=len(files),
        passed=total_score < config.fail_threshold,
    )
