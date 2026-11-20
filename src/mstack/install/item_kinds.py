"""What each kind of mstack item is, where it installs, and how it is hashed.

Copied kinds (skill, rule, agent) own a file or folder inside a target folder.
Merged kinds (mcp, settings, instructions) own only part of a shared file: the keys
of a JSON fragment, or the managed block of a Markdown file. Their installed hash
covers only that part, so the user's own keys and text never change their state.
"""

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from mstack.install.hashing import hash_installed, hash_text, hash_tree
from mstack.install.merge import (
    MergeError,
    extract_block,
    leaf_keys,
    load_json_object,
    nest,
    project,
)
from mstack.install.render import RuleFormatError, render_rule
from mstack.platform import tool_homes

Kind = Literal["skill", "rule", "agent", "mcp", "settings", "instructions"]
Tool = Literal["claude", "cursor", "both"]
KINDS: tuple[Kind, ...] = ("skill", "rule", "agent", "mcp", "settings", "instructions")
COPIED_KINDS = frozenset({"skill", "rule", "agent"})

# This skill runs from the checkout and is never installed.
NOT_INSTALLED_SKILLS = frozenset({"setup-mstack"})
FOLDER_README = "README.md"
GLOBAL_INSTRUCTIONS = "global"
CLAUDE_SETTINGS = "claude"


class SourceError(Exception):
    """A source item in the checkout cannot be read."""


class SourceItem(BaseModel):
    kind: Kind
    name: str
    source_hash: str
    target: Path


def expand(target: str | Path) -> Path:
    return Path(os.path.abspath(Path(target).expanduser()))


def uses_claude(tool: Tool) -> bool:
    return tool in {"claude", "both"}


def uses_cursor(tool: Tool) -> bool:
    return tool in {"cursor", "both"}


def target_locations(kind: Kind, tool: Tool) -> list[Path]:
    """Folders a copied kind installs into, or files a merged kind merges into.

    With both tools, skills and agents go to ~/.claude only: Cursor also loads those
    folders, and a second copy would show every item twice. On WSL, Cursor runs on
    Windows and reads the Windows profile, so there both tools get their own copy.
    """
    homes = tool_homes()
    claude, cursor = homes["claude"] / ".claude", homes["cursor"] / ".cursor"
    separate_homes = homes["claude"] != homes["cursor"]
    copies_for_cursor = uses_cursor(tool) and (not uses_claude(tool) or separate_homes)

    def copied(folder: str) -> list[Path]:
        return [claude / folder] * uses_claude(tool) + [
            cursor / folder
        ] * copies_for_cursor

    locations = {
        "skill": copied("skills"),
        "agent": copied("agents"),
        "rule": [claude / "rules"] if uses_claude(tool) else [],
        "mcp": [homes["claude"] / ".claude.json"] * uses_claude(tool)
        + [cursor / "mcp.json"] * uses_cursor(tool),
        "settings": [claude / "settings.json"] if uses_claude(tool) else [],
        "instructions": [claude / "CLAUDE.md"] if uses_claude(tool) else [],
    }
    return [expand(location) for location in locations[kind]]


def source_names(checkout: Path, kind: Kind) -> list[str]:
    if kind == "skill":
        return [
            skill.parent.name
            for skill in sorted((checkout / "skills").glob("*/SKILL.md"))
            if skill.parent.name not in NOT_INSTALLED_SKILLS
        ]
    if kind == "rule":
        return [mdc.stem for mdc in sorted((checkout / "rules").glob("*.mdc"))]
    if kind == "agent":
        return [
            path.stem
            for path in sorted((checkout / "agents").glob("*.md"))
            if path.name != FOLDER_README
        ]
    if kind == "mcp":
        return [path.stem for path in sorted((checkout / "mcp").glob("*.json"))]
    if kind == "settings":
        present = (checkout / "settings" / f"{CLAUDE_SETTINGS}.json").is_file()
        return [CLAUDE_SETTINGS] if present else []
    present = (checkout / "instructions" / f"{GLOBAL_INSTRUCTIONS}.md").is_file()
    return [GLOBAL_INSTRUCTIONS] if present else []


def item_target(kind: Kind, name: str, location: Path) -> Path:
    if kind == "skill":
        return location / name
    if kind in COPIED_KINDS:
        return location / f"{name}.md"
    return location


def source_fragment(checkout: Path, kind: Kind, name: str) -> Any:
    """A merged JSON fragment nested the way it sits in its target file."""
    fragment = load_json_object(checkout / kind / f"{name}.json")
    return nest(fragment, ["mcpServers", name] if kind == "mcp" else [])


def hash_json(value: Any) -> str:
    return hash_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def normalized_block(text: str) -> str:
    return text.strip("\n") + "\n"


def source_hash(checkout: Path, kind: Kind, name: str) -> str:
    try:
        if kind == "skill":
            return hash_tree(checkout / "skills" / name)
        if kind == "rule":
            mdc = checkout / "rules" / f"{name}.mdc"
            return hash_text(render_rule(mdc.read_text(encoding="utf-8")))
        if kind == "agent":
            agent_hash = hash_installed(checkout / "agents" / f"{name}.md")
            if agent_hash is None:
                raise SourceError(f"no agents/{name}.md in the checkout")
            return agent_hash
        if kind == "instructions":
            path = checkout / "instructions" / f"{name}.md"
            return hash_text(normalized_block(path.read_text(encoding="utf-8")))
        return hash_json(source_fragment(checkout, kind, name))
    except (OSError, RuleFormatError, MergeError) as error:
        raise SourceError(f"cannot read the source {kind} {name}: {error}") from error


def installed_hash(checkout: Path, kind: Kind, name: str, target: Path) -> str | None:
    """Hash of what mstack owns at the target, or None when none of it is there."""
    if kind in COPIED_KINDS:
        return hash_installed(target)
    if not target.is_file():
        return None
    if kind == "instructions":
        block = extract_block(target.read_text(encoding="utf-8"))
        return None if block is None else hash_text(normalized_block(block))
    try:
        installed = load_json_object(target)
    except MergeError as error:
        raise SourceError(str(error)) from error
    projected = project(installed, source_fragment(checkout, kind, name))
    return None if projected is None else hash_json(projected)


def written_keys(checkout: Path, kind: Kind, name: str) -> list[str] | None:
    """The JSON keys mstack writes for a merged item, recorded for a later removal."""
    if kind not in {"mcp", "settings"}:
        return None
    return leaf_keys(source_fragment(checkout, kind, name))


def source_items(checkout: Path, tool: Tool) -> list[SourceItem]:
    return [
        SourceItem(
            kind=kind,
            name=name,
            source_hash=source_hash(checkout, kind, name),
            target=item_target(kind, name, location),
        )
        for kind in KINDS
        for location in target_locations(kind, tool)
        for name in source_names(checkout, kind)
    ]


def owns_target(kind: Kind, target: Path, tool: Tool) -> bool:
    """Whether a recorded target belongs to the locations the tool selection covers."""
    locations = target_locations(kind, tool)
    if kind in COPIED_KINDS:
        return target.parent in locations
    return target in locations
