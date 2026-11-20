import hashlib
from pathlib import Path

# The same names the setup-mstack skill ignores when it compares skills.
IGNORED_NAMES = frozenset({".DS_Store", "__pycache__"})
HASH_PREFIX = "sha256:"


def file_content(path: Path) -> bytes:
    """A file's bytes with CRLF read as LF: a copy written on Windows is the same item."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def is_ignored(relative_path: Path) -> bool:
    return any(part in IGNORED_NAMES for part in relative_path.parts)


def tree_files(root: Path) -> list[Path]:
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and not is_ignored(path.relative_to(root))
    )


def hash_tree(root: Path) -> str:
    """Hash the sorted relative paths and contents of every file under root."""
    digest = hashlib.sha256()
    for relative_path in tree_files(root):
        content = file_content(root / relative_path)
        digest.update(relative_path.as_posix().encode("utf-8") + b"\0")
        digest.update(str(len(content)).encode("ascii") + b"\0")
        digest.update(content)
    return HASH_PREFIX + digest.hexdigest()


def hash_text(text: str) -> str:
    return HASH_PREFIX + hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_installed(target: Path) -> str | None:
    """Hash a skill folder or a rule file, or None when nothing is installed."""
    if target.is_dir():
        return hash_tree(target)
    if target.is_file():
        return HASH_PREFIX + hashlib.sha256(file_content(target)).hexdigest()
    return None
