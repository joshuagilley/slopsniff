import re
from collections import defaultdict

from ..models import FileContext, Finding

_HELPER_FILENAMES = frozenset(
    {"utils", "helpers", "common", "shared", "misc", "util", "helper"}
)

# Strip version/variant suffixes to find the base name
_VERSION_RE = re.compile(
    r"(_v\d+\w*|_safe|_new|_old|_legacy|_fixed|_updated|_temp|_tmp|_copy)$"
)


def _base_name(name: str) -> str:
    return _VERSION_RE.sub("", name)


class HelperSprawlRule:
    rule_id = "helper-sprawl"
    description = (
        "Flags generic helper file names and versioned/duplicate function name patterns"
    )

    def run(self, file_context: FileContext) -> list[Finding]:
        stem = file_context.path.stem.lower()
        if stem in _HELPER_FILENAMES:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity="low",
                    file_path=str(file_context.path),
                    line_start=None,
                    line_end=None,
                    message=(
                        f"Generic helper filename '{file_context.path.name}' suggests "
                        "a low-cohesion catch-all module"
                    ),
                    score=2,
                )
            ]
        return []

    def run_cross_file(self, contexts: list[FileContext]) -> list[Finding]:
        """Flag clusters of versioned function names sharing the same base."""
        base_map: dict[str, list[tuple[str, str, int]]] = defaultdict(list)

        for ctx in contexts:
            for fn in ctx.functions:
                base_map[_base_name(fn.name)].append(
                    (fn.name, fn.file_path, fn.line_start)
                )

        findings: list[Finding] = []
        for base, variants in base_map.items():
            unique_names = {name for name, _, _ in variants}
            if len(unique_names) < 2:
                continue

            locations = ", ".join(
                f"'{name}' at {path}:{line}" for name, path, line in variants
            )
            primary_name, primary_path, primary_line = variants[0]
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity="medium",
                    file_path=primary_path,
                    line_start=primary_line,
                    line_end=None,
                    message=(
                        f"Versioned function name variants detected for '{base}': "
                        f"{locations}"
                    ),
                    score=5,
                )
            )

        return findings
