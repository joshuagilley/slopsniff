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


def test_walk_excludes_tests_dir_by_default(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_config.py").write_text('x = os.getenv("X", "1")')
    (tmp_path / "src.py").write_text("x = 1")

    config = Config()
    files = walk_repo(tmp_path, config)

    assert not any("tests" in f.parts for f in files)
    assert any(f.name == "src.py" for f in files)


def test_walk_filters_by_extension(tmp_path: Path) -> None:
    (tmp_path / "script.py").write_text("x = 1")
    (tmp_path / "readme.md").write_text("# readme")
    (tmp_path / "guide.mdx").write_text("# mdx")
    (tmp_path / "notes.txt").write_text("some notes")

    config = Config()
    files = walk_repo(tmp_path, config)

    extensions = {f.suffix for f in files}
    assert ".py" in extensions
    assert ".md" not in extensions
    assert ".mdx" not in extensions
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


def test_walk_excludes_specific_file_by_name(tmp_path: Path) -> None:
    (tmp_path / "temp_slop_examples.py").write_text("x = 1")
    (tmp_path / "keep.py").write_text("y = 2")

    config = Config(exclude_files=["temp_slop_examples.py"])
    files = walk_repo(tmp_path, config)

    assert not any(f.name == "temp_slop_examples.py" for f in files)
    assert any(f.name == "keep.py" for f in files)


def test_walk_excludes_specific_file_by_relative_path(tmp_path: Path) -> None:
    nested = tmp_path / "src" / "fixtures"
    nested.mkdir(parents=True)
    (nested / "example.py").write_text("x = 1")
    (tmp_path / "src" / "main.py").write_text("y = 2")

    config = Config(exclude_files=["src/fixtures/example.py"])
    files = walk_repo(tmp_path, config)

    assert not any(str(f).endswith("src/fixtures/example.py") for f in files)
    assert any(str(f).endswith("src/main.py") for f in files)
