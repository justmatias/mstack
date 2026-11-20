from pathlib import Path

from mstack.install.hashing import hash_installed, hash_tree


def write_tree(root: Path, files: dict[str, str]) -> Path:
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def test_hash_does_not_depend_on_creation_order(tmp_path: Path):
    first = write_tree(tmp_path / "first", {"a.md": "A", "b/c.md": "C"})
    second = write_tree(tmp_path / "second", {"b/c.md": "C", "a.md": "A"})

    assert hash_tree(first) == hash_tree(second)


def test_ignored_files_do_not_change_the_hash(tmp_path: Path):
    clean = write_tree(tmp_path / "clean", {"a.md": "A"})
    noisy = write_tree(
        tmp_path / "noisy",
        {"a.md": "A", ".DS_Store": "x", "__pycache__/m.cpython-312.pyc": "y"},
    )

    assert hash_tree(clean) == hash_tree(noisy)


def test_one_byte_changes_the_hash(tmp_path: Path):
    original = write_tree(tmp_path / "original", {"a.md": "A"})
    changed = write_tree(tmp_path / "changed", {"a.md": "B"})

    assert hash_tree(original) != hash_tree(changed)


def test_renaming_a_file_changes_the_hash(tmp_path: Path):
    original = write_tree(tmp_path / "original", {"a.md": "A"})
    renamed = write_tree(tmp_path / "renamed", {"b.md": "A"})

    assert hash_tree(original) != hash_tree(renamed)


def test_nothing_installed_has_no_hash(tmp_path: Path):
    assert hash_installed(tmp_path / "missing") is None


def test_line_endings_do_not_change_the_hash(tmp_path: Path):
    unix = tmp_path / "unix"
    windows = tmp_path / "windows"
    for root, newline in ((unix, b"\n"), (windows, b"\r\n")):
        (root / "references").mkdir(parents=True)
        (root / "SKILL.md").write_bytes(b"# Skill" + newline + b"Body" + newline)
        (root / "references" / "notes.md").write_bytes(b"Notes" + newline)

    assert hash_tree(unix) == hash_tree(windows)
    assert hash_installed(unix / "SKILL.md") == hash_installed(windows / "SKILL.md")


def test_content_changes_still_change_the_hash(tmp_path: Path):
    first = write_tree(tmp_path / "first", {"a.md": "A\n"})
    second = write_tree(tmp_path / "second", {"a.md": "B\n"})

    assert hash_tree(first) != hash_tree(second)
