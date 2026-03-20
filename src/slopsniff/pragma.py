"""Detect inline ignore pragmas on a source line."""

from __future__ import annotations

import re

# Matches slopsniff: ignore OR slopsniff: ignore rule-id OR slopsniff: ignore a, b
_IGNORE_RE = re.compile(
    r"slopsniff:\s*ignore(?:\s+([\w\-]+(?:\s*,\s*[\w\-]+)*))?",
    re.IGNORECASE,
)


def line_ignores_rule(line: str, rule_id: str) -> bool:
    """True if ``line`` contains a pragma that suppresses ``rule_id``.

    - ``slopsniff: ignore`` — suppresses all rules that consult this helper.
    - ``slopsniff: ignore exposed-secrets`` — suppresses only that rule.
    - ``slopsniff: ignore exposed-secrets, large-file`` — listed rules only.

    The pragma may appear anywhere on the line (e.g. after ``#`` or ``//``).
    If the line is edited, re-run slopsniff; removing or changing the pragma
    or the sensitive text will surface findings again.
    """
    for m in _IGNORE_RE.finditer(line):
        rest = (m.group(1) or "").strip()
        if not rest:
            return True
        listed = {p.strip() for p in rest.split(",") if p.strip()}
        if rule_id in listed:
            return True
    return False
