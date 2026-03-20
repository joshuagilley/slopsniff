import json
from dataclasses import asdict

from ..models import ScanResult
from ..scoring import grade


def report(result: ScanResult) -> str:
    data = {
        "files_scanned": result.files_scanned,
        "total_score": result.total_score,
        "status": grade(result.total_score),
        "passed": result.passed,
        "findings": [asdict(f) for f in result.findings],
    }
    return json.dumps(data, indent=2)
