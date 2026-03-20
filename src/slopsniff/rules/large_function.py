from ..config import Config
from ..models import FileContext, Finding


class LargeFunctionRule:
    rule_id = "large-function"
    description = "Flags functions that exceed configurable line count thresholds"

    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self, file_context: FileContext) -> list[Finding]:
        findings: list[Finding] = []

        for fn in file_context.functions:
            length = fn.line_end - fn.line_start + 1

            if length >= self.config.max_function_lines_high:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity="high",
                        file_path=str(file_context.path),
                        line_start=fn.line_start,
                        line_end=fn.line_end,
                        message=(
                            f"Function '{fn.name}' is {length} lines long "
                            f"(high threshold: {self.config.max_function_lines_high})"
                        ),
                        score=10,
                    )
                )
            elif length >= self.config.max_function_lines_warning:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity="medium",
                        file_path=str(file_context.path),
                        line_start=fn.line_start,
                        line_end=fn.line_end,
                        message=(
                            f"Function '{fn.name}' is {length} lines long "
                            f"(warning threshold: {self.config.max_function_lines_warning})"
                        ),
                        score=5,
                    )
                )

        return findings
