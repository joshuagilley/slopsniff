from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Finding:
    rule_id: str
    severity: str  # "low", "medium", "high"
    file_path: str
    line_start: int | None
    line_end: int | None
    message: str
    score: int


@dataclass
class FunctionInfo:
    name: str
    file_path: str
    line_start: int
    line_end: int
    body_hash: str


@dataclass
class FileContext:
    path: Path
    lines: list[str]
    language: str
    functions: list[FunctionInfo] = field(default_factory=list)


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    total_score: int = 0
    files_scanned: int = 0
    passed: bool = True
