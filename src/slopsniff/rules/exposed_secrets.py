"""Heuristic detection of strings that look like real credentials (not AI detection)."""

from __future__ import annotations

import re

from ..models import FileContext, Finding
from ..pragma import line_ignores_rule

# High-confidence shapes only; favor missing a secret over drowning blogs/CI in noise.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "PEM private key header",
        re.compile(r"-----BEGIN [A-Z0-9 +\-]+PRIVATE KEY-----"),
    ),
    (
        "AWS access key id",
        re.compile(r"\b(?:AKIA|ASIA|AROA)[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub personal access token (classic)",
        re.compile(r"\bghp_[a-zA-Z0-9]{36,}\b"),
    ),
    (
        "GitHub fine-grained PAT",
        re.compile(r"github_pat_[a-zA-Z0-9_]{20,}"),
    ),
    (
        "Slack bot/user token",
        re.compile(r"xox[bpa]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}"),
    ),
    (
        "Stripe secret key",
        re.compile(r"\bsk_(?:live|test)_[0-9a-zA-Z]{20,}\b"),
    ),
    (
        "OpenAI API key (sk-proj-)",
        re.compile(r"\bsk-proj-[a-zA-Z0-9_-]{20,}\b"),
    ),
    (
        "OpenAI-style API key (long sk- prefix)",
        re.compile(r"\bsk-[a-zA-Z0-9]{45,}\b"),
    ),
    (
        "Anthropic API key",
        re.compile(r"\bsk-ant-api03-[a-zA-Z0-9_-]{20,}\b"),
    ),
    (
        "Google API key",
        re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    ),
    (
        "SendGrid API key",
        re.compile(r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{40,}"),
    ),
]


class ExposedSecretsRule:
    rule_id = "exposed-secrets"
    description = "Flags lines that resemble common secret/token formats in source or content files"

    def run(self, file_context: FileContext) -> list[Finding]:
        findings: list[Finding] = []
        seen_lines: set[int] = set()

        for i, line in enumerate(file_context.lines, start=1):
            if i in seen_lines:
                continue
            kinds: list[str] = []
            for label, pattern in _PATTERNS:
                if pattern.search(line):
                    kinds.append(label)
            if not kinds:
                continue
            if line_ignores_rule(line, self.rule_id):
                continue
            seen_lines.add(i)
            kinds_str = "; ".join(kinds) if len(kinds) > 1 else kinds[0]
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity="high",
                    file_path=str(file_context.path),
                    line_start=i,
                    line_end=i,
                    message=(
                        f"Possible exposed secret ({kinds_str}). "
                        "Remove or rotate the credential; use env vars or a secret manager."
                    ),
                    score=10,
                )
            )

        return findings
