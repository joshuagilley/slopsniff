from pathlib import Path

from .config import Config


def walk_repo(root: Path, config: Config) -> list[Path]:
    files: list[Path] = []
    exclude_file_set = set(config.exclude_files)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(excluded in path.parts for excluded in config.exclude_dirs):
            continue
        relative = path.relative_to(root).as_posix()
        if path.name in exclude_file_set or relative in exclude_file_set:
            continue
        if path.suffix in config.include_extensions:
            files.append(path)
    return sorted(files)
