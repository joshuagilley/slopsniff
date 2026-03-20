from ..config import Config
from ..models import FileContext, Finding


class LargeFileRule:
    rule_id = "large-file"
    description = "Flags files that exceed configurable line count thresholds"

    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self, file_context: FileContext) -> list[Finding]:
        suffix = file_context.path.suffix.lower()
        if suffix not in self.config.large_file_extensions:
            return []

        count = len(file_context.lines)

        if count >= self.config.max_file_lines_high:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity="high",
                    file_path=str(file_context.path),
                    line_start=None,
                    line_end=None,
                    message=(
                        f"File is {count} lines long "
                        f"(high threshold: {self.config.max_file_lines_high})"
                    ),
                    score=10,
                )
            ]

        if count >= self.config.max_file_lines_warning:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity="medium",
                    file_path=str(file_context.path),
                    line_start=None,
                    line_end=None,
                    message=(
                        f"File is {count} lines long "
                        f"(warning threshold: {self.config.max_file_lines_warning})"
                    ),
                    score=5,
                )
            ]

        return []
