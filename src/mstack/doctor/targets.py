"""What mstack ships in the checkout, and the folders each tool loads it from.

With both tools, skills and agents go to ~/.claude only: Cursor also loads those
folders, and a second copy would show every item twice. On WSL, Cursor runs on
Windows and reads the Windows profile, so there both tools get their own copy.
"""

from pathlib import Path
from typing import Literal

Tool = Literal["claude", "cursor", "both"]
FOLDER_README = "README.md"
# Names that a copy may carry and that never make it differ from the checkout.
IGNORED_NAMES = frozenset({".DS_Store", "__pycache__", ".mstack-backups"})


def uses_claude(tool: Tool) -> bool:
    return tool in {"claude", "both"}


def uses_cursor(tool: Tool) -> bool:
    return tool in {"cursor", "both"}


def copied_folders(
    tool: Tool, home: Path, cursor_home: Path, folder: str
) -> list[Path]:
    """The folders a copied kind (skills, agents) installs into."""
    claude = home / ".claude" / folder
    cursor = cursor_home / ".cursor" / folder
    if not uses_cursor(tool):
        return [claude]
    if not uses_claude(tool):
        return [cursor]
    return [claude, cursor] if cursor_home != home else [claude]


def skill_names(checkout: Path) -> list[str]:
    return [
        skill.parent.name for skill in sorted((checkout / "skills").glob("*/SKILL.md"))
    ]


def rule_names(checkout: Path) -> list[str]:
    return [mdc.stem for mdc in sorted((checkout / "rules").glob("*.mdc"))]


def agent_names(checkout: Path) -> list[str]:
    return [
        path.stem
        for path in sorted((checkout / "agents").glob("*.md"))
        if path.name != FOLDER_README
    ]


def file_content(path: Path) -> bytes:
    """A file's bytes with CRLF read as LF: a copy written on Windows is the same."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def tree_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): file_content(path)
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_NAMES for part in path.relative_to(root).parts)
    }


def same_tree(source: Path, installed: Path) -> bool:
    return tree_files(source) == tree_files(installed)
