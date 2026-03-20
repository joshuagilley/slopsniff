from pathlib import Path

from .config import Config


def walk_repo(root: Path, config: Config) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(excluded in path.parts for excluded in config.exclude_dirs):
            continue
        if path.suffix in config.include_extensions:
            files.append(path)
    return sorted(files)
