"""What mstack ships in the checkout, and the folders each tool loads it from.

With both tools, skills and agents go to ~/.claude only: Cursor also loads those
folders, and a second copy would show every item twice. On WSL, Cursor runs on
Windows and reads the Windows profile, so there both tools get their own copy.
"""

from pathlib import Path

TOOLS = ("claude", "cursor", "codex")
FOLDER_README = "README.md"
# Names that a copy may carry and that never make it differ from the checkout.
IGNORED_NAMES = frozenset({".DS_Store", "__pycache__", ".mstack-backups"})


def selected_tools(tool: str) -> set[str]:
    return {"claude", "cursor"} if tool == "both" else set(tool.split(","))


def uses_claude(tool: str) -> bool:
    return "claude" in selected_tools(tool)


def uses_cursor(tool: str) -> bool:
    return "cursor" in selected_tools(tool)


def uses_codex(tool: str) -> bool:
    return "codex" in selected_tools(tool)


def copied_folders(tool: str, home: Path, cursor_home: Path, folder: str) -> list[Path]:
    """The folders a copied kind (skills, agents) installs into."""
    claude = home / ".claude" / folder
    cursor = cursor_home / ".cursor" / folder
    if not uses_cursor(tool):
        return [claude] if uses_claude(tool) else []
    if not uses_claude(tool):
        return [cursor]
    return [claude, cursor] if cursor_home != home else [claude]


def skill_folders(tool: str, home: Path, cursor_home: Path) -> list[Path]:
    folders = copied_folders(tool, home, cursor_home, "skills")
    if not uses_codex(tool):
        return folders
    # https://developers.openai.com/codex/skills
    # https://cursor.com/docs/skills
    shared = home / ".agents" / "skills"
    if cursor_home == home:
        folders = [
            folder for folder in folders if folder != home / ".cursor" / "skills"
        ]
    return [*folders, shared]


def codex_instructions(folder: Path) -> Path:
    override = folder / "AGENTS.override.md"
    if override.is_file() and override.read_bytes().strip():
        return override
    return folder / "AGENTS.md"


def skill_sources(checkout: Path) -> dict[str, Path]:
    """Each skill's folder in the checkout, by name.

    The checkout groups skills by topic (`skills/<group>/<name>`), but they are
    installed flat, so the name is the key and the group is not part of it.
    """
    skills_folder = checkout / "skills"
    folders = [*skills_folder.glob("*/SKILL.md"), *skills_folder.glob("*/*/SKILL.md")]
    return {path.parent.name: path.parent for path in sorted(folders)}


def skill_names(checkout: Path) -> list[str]:
    return list(skill_sources(checkout))


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
