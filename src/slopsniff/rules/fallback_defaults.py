"""Detect fallback patterns that are likely to mask correctness bugs."""

from __future__ import annotations

import re

from ..models import FileContext, Finding
from ..pragma import line_ignores_rule

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Python env fallback to primitive sentinel",
        re.compile(
            r"""\bos\.(?:getenv|environ\.get|getenv)\s*\(\s*['"][A-Z0-9_]+['"]\s*,\s*"""
            r"""(?:None|True|False|0|1|['"]{2}|\[\]|\{\})\s*\)"""
        ),
    ),
    (
        "dotenv env fallback to primitive sentinel",
        re.compile(
            r"""\bdotenv\.get\s*\(\s*['"][A-Z0-9_]+['"]\s*,\s*"""
            r"""(?:None|True|False|0|1|['"]{2}|\[\]|\{\})\s*\)"""
        ),
    ),
    (
        "Node process.env logical-or primitive fallback",
        re.compile(
            r"""\bprocess\.env\.[A-Z0-9_]+\s*\|\|\s*"""
            r"""(?:null|undefined|true|false|0|1|['"]{2}|\[\]|\{\})"""
        ),
    ),
    (
        "Node process.env nullish primitive fallback",
        re.compile(
            r"""\bprocess\.env\.[A-Z0-9_]+\s*\?\?\s*"""
            r"""(?:null|undefined|true|false|0|1|['"]{2}|\[\]|\{\})"""
        ),
    ),
    (
        "Python catch-all returns primitive",
        re.compile(
            r"""\bexcept(?:\s+(?:Exception|BaseException))?(?:\s+as\s+\w+)?\s*:\s*"""
            r"""return\s+(?:None|True|False|0|1|['"]{2}|\[\]|\{\})"""
        ),
    ),
    (
        "JS catch-all returns primitive",
        re.compile(
            r"""\bcatch\s*(?:\(\s*\w+\s*\))?\s*\{\s*return\s*"""
            r"""(?:null|undefined|true|false|0|1|['"]{2}|\[\]|\{\})\s*;?\s*\}"""
        ),
    ),
]


class FallbackDefaultsRule:
    rule_id = "fallback-defaults"
    description = (
        "Flags likely bug-masking fallbacks: primitive env defaults and catch-all primitive returns"
    )

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
                    severity="medium",
                    file_path=str(file_context.path),
                    line_start=i,
                    line_end=i,
                    message=(
                        f"Potential slop fallback detected ({kinds_str}). "
                        "Avoid silent primitive defaults; "
                        "preserve failure semantics or add observability."
                    ),
                    score=4,
                )
            )

        return findings
