from pathlib import Path

from slopsniff.config import Config
from slopsniff.walker import walk_repo


def test_walk_excludes_git_dir(tmp_path: Path) -> None:
    # Only create the .git dir itself; avoid writing inside it (OS-protected on some systems)
    (tmp_path / ".git").mkdir()
    (tmp_path / "main.py").write_text("x = 1")

    config = Config()
    files = walk_repo(tmp_path, config)

    assert all(".git" not in str(f) for f in files)
    assert any(f.name == "main.py" for f in files)


def test_walk_excludes_node_modules(tmp_path: Path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lodash.js").write_text("// lodash")
    (tmp_path / "index.ts").write_text("const x = 1")

    config = Config()
    files = walk_repo(tmp_path, config)

    assert not any("node_modules" in str(f) for f in files)
    assert any(f.name == "index.ts" for f in files)


def test_walk_filters_by_extension(tmp_path: Path) -> None:
    (tmp_path / "script.py").write_text("x = 1")
    (tmp_path / "readme.md").write_text("# readme")
    (tmp_path / "notes.txt").write_text("some notes")

    config = Config()
    files = walk_repo(tmp_path, config)

    extensions = {f.suffix for f in files}
    assert ".py" in extensions
    assert ".md" in extensions
    assert ".txt" not in extensions


def test_walk_returns_sorted_paths(tmp_path: Path) -> None:
    (tmp_path / "b.py").write_text("b = 2")
    (tmp_path / "a.py").write_text("a = 1")

    config = Config()
    files = walk_repo(tmp_path, config)

    assert files == sorted(files)


def test_walk_includes_nested_files(tmp_path: Path) -> None:
    subdir = tmp_path / "src" / "api"
    subdir.mkdir(parents=True)
    (subdir / "routes.py").write_text("routes = []")

    config = Config()
    files = walk_repo(tmp_path, config)

    assert any(f.name == "routes.py" for f in files)
