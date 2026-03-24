from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .models import FileContext, Finding, ScanResult
from .parsers.python_ast import parse_python
from .parsers.text_parser import parse_text
from .rules.base import CrossFileRule, PerFileRule
from .rules.duplicate_functions import DuplicateFunctionsRule
from .rules.exposed_secrets import ExposedSecretsRule
from .rules.fallback_defaults import FallbackDefaultsRule
from .rules.helper_sprawl import HelperSprawlRule
from .rules.large_file import LargeFileRule
from .rules.large_function import LargeFunctionRule
from .scoring import compute_score
from .walker import walk_repo


@dataclass(frozen=True)
class RuleSet:
    per_file: dict[str, PerFileRule]
    cross_file: dict[str, CrossFileRule]

    @property
    def all_rule_ids(self) -> set[str]:
        return set(self.per_file) | set(self.cross_file)


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


def _build_rule_set(config: Config) -> RuleSet:
    large_file_rule = LargeFileRule(config)
    large_fn_rule = LargeFunctionRule(config)
    duplicate_rule = DuplicateFunctionsRule()
    sprawl_rule = HelperSprawlRule()
    secrets_rule = ExposedSecretsRule()
    fallback_rule = FallbackDefaultsRule()

    return RuleSet(
        per_file={
            large_file_rule.rule_id: large_file_rule,
            large_fn_rule.rule_id: large_fn_rule,
            sprawl_rule.rule_id: sprawl_rule,
            secrets_rule.rule_id: secrets_rule,
            fallback_rule.rule_id: fallback_rule,
        },
        cross_file={
            duplicate_rule.rule_id: duplicate_rule,
            sprawl_rule.rule_id: sprawl_rule,
        },
    )


def _resolve_enabled_rule_ids(config: Config, available_rule_ids: set[str]) -> set[str]:
    enabled_rule_ids = set(config.include_rules or available_rule_ids)
    unknown_rule_ids = enabled_rule_ids - available_rule_ids
    if unknown_rule_ids:
        unknown = ", ".join(sorted(unknown_rule_ids))
        raise ValueError(f"Unknown rule id(s) in config include list: {unknown}")
    return enabled_rule_ids


def _build_contexts(files: list[Path]) -> list[FileContext]:
    contexts: list[FileContext] = []
    for file_path in files:
        ctx = _build_context(file_path)
        if ctx is not None:
            contexts.append(ctx)
    return contexts


def _run_per_file_rules(
    contexts: list[FileContext],
    rules: dict[str, PerFileRule],
    enabled_rule_ids: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    for ctx in contexts:
        for rule_id, rule in rules.items():
            if rule_id in enabled_rule_ids:
                findings.extend(rule.run(ctx))
    return findings


def _run_cross_file_rules(
    contexts: list[FileContext],
    rules: dict[str, CrossFileRule],
    enabled_rule_ids: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    for rule_id, rule in rules.items():
        if rule_id in enabled_rule_ids:
            findings.extend(rule.run_cross_file(contexts))
    return findings


def scan(root: Path, config: Config) -> ScanResult:
    files = walk_repo(root, config)
    rule_set = _build_rule_set(config)
    enabled_rule_ids = _resolve_enabled_rule_ids(config, rule_set.all_rule_ids)
    contexts = _build_contexts(files)
    findings = [
        *_run_per_file_rules(contexts, rule_set.per_file, enabled_rule_ids),
        *_run_cross_file_rules(contexts, rule_set.cross_file, enabled_rule_ids),
    ]
    total_score = compute_score(findings)
    return ScanResult(
        findings=findings,
        total_score=total_score,
        files_scanned=len(contexts),
        passed=total_score <= config.fail_threshold,
    )
