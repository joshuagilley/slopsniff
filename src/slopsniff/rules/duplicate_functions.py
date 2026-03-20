from collections import defaultdict

from ..models import FileContext, Finding, FunctionInfo

# Ignore trivially small functions to reduce noise (e.g. empty __init__)
_MIN_LINES = 5


class DuplicateFunctionsRule:
    rule_id = "duplicate-functions"
    description = "Flags function bodies that are exact duplicates across or within files"

    def run_cross_file(self, contexts: list[FileContext]) -> list[Finding]:
        hash_map: dict[str, list[FunctionInfo]] = defaultdict(list)

        for ctx in contexts:
            for fn in ctx.functions:
                if fn.line_end - fn.line_start + 1 < _MIN_LINES:
                    continue
                hash_map[fn.body_hash].append(fn)

        findings: list[Finding] = []
        for fns in hash_map.values():
            if len(fns) < 2:
                continue

            locations = ", ".join(f"{fn.file_path}:{fn.line_start}-{fn.line_end}" for fn in fns)
            primary = fns[0]
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity="high",
                    file_path=primary.file_path,
                    line_start=primary.line_start,
                    line_end=primary.line_end,
                    message=(f"Duplicate function body found in {len(fns)} locations: {locations}"),
                    score=10,
                )
            )

        return findings
