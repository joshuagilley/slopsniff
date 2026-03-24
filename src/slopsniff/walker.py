from pathlib import Path

from .config import Config


def path_matches_scan(root: Path, path: Path, config: Config) -> bool:
    """Whether ``path`` is a regular file under ``root`` that config says we should scan."""
    root = root.resolve()
    path = path.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return False
    if not path.is_file():
        return False
    if any(excluded in path.parts for excluded in config.exclude_dirs):
        return False
    relative = path.relative_to(root).as_posix()
    exclude_file_set = set(config.exclude_files)
    if path.name in exclude_file_set or relative in exclude_file_set:
        return False
    return path.suffix in config.include_extensions


def walk_repo(root: Path, config: Config) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        if path_matches_scan(root, path, config):
            files.append(path.resolve())
    return sorted(files)
