from typing import Protocol

from ..models import FileContext, Finding


class PerFileRule(Protocol):
    rule_id: str
    description: str

    def run(self, file_context: FileContext) -> list[Finding]: ...


class CrossFileRule(Protocol):
    rule_id: str
    description: str

    def run_cross_file(self, contexts: list[FileContext]) -> list[Finding]: ...
