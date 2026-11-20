import argparse
import copy
import json
import logging
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from mstack.install.files import atomic_write_text

logger = logging.getLogger(__name__)

BLOCK_BEGIN = "<!-- mstack:begin -->"
BLOCK_END = "<!-- mstack:end -->"


class MergeError(ValueError):
    """A fragment or target cannot be merged."""


class Change(BaseModel):
    key: str
    action: Literal["add", "change", "extend"]
    old: Any = None
    new: Any = None


def key_name(path: tuple[str, ...]) -> str:
    return ".".join(path)


def union(base: list, fragment: list) -> list:
    return base + [item for item in fragment if item not in base]


def deep_merge(
    base: Any, fragment: Any, path: tuple[str, ...] = ()
) -> tuple[Any, list[Change]]:
    """Merge fragment into base: objects by key, arrays as unions, fragment scalars win.

    Keys the fragment does not define are never touched. Neither input is modified.
    """
    if isinstance(base, dict) and isinstance(fragment, dict):
        merged = dict(base)
        changes: list[Change] = []
        for key, value in fragment.items():
            if key not in base:
                merged[key] = copy.deepcopy(value)
                changes.append(
                    Change(key=key_name((*path, key)), action="add", new=value)
                )
                continue
            merged[key], nested = deep_merge(base[key], value, (*path, key))
            changes.extend(nested)
        return merged, changes
    if isinstance(base, list) and isinstance(fragment, list):
        merged_list = union(base, fragment)
        added = merged_list[len(base) :]
        if not added:
            return base, []
        return merged_list, [Change(key=key_name(path), action="extend", new=added)]
    if base == fragment:
        return base, []
    return copy.deepcopy(fragment), [
        Change(key=key_name(path), action="change", old=base, new=fragment)
    ]


def project(target: Any, fragment: Any) -> Any:
    """The part of target that the fragment defines, or None when none of it is there.

    Equal to the fragment exactly when merging it would change nothing.
    """
    if isinstance(fragment, dict):
        if not isinstance(target, dict):
            return None
        projected = {}
        for key, value in fragment.items():
            if key in target:
                nested = project(target[key], value)
                if nested is not None:
                    projected[key] = nested
        return projected or None
    if isinstance(fragment, list):
        if not isinstance(target, list):
            return None
        return [item for item in fragment if item in target] or None
    return target


def leaf_keys(fragment: Any, path: tuple[str, ...] = ()) -> list[str]:
    if isinstance(fragment, dict) and fragment:
        return [
            key
            for name, value in fragment.items()
            for key in leaf_keys(value, (*path, name))
        ]
    return [key_name(path)]


def nest(fragment: Any, under: list[str]) -> Any:
    for key in reversed(under):
        fragment = {key: fragment}
    return fragment


def load_json_object(path: Path, *, missing_ok: bool = False) -> dict:
    if missing_ok and not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MergeError(f"cannot read {path}: {error}") from error
    if not isinstance(data, dict):
        raise MergeError(f"{path} is not a JSON object")
    return data


def extract_block(text: str) -> str | None:
    """The text between the mstack markers, or None when there is no block."""
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start == -1 or end == -1 or end < start:
        return None
    return text[start + len(BLOCK_BEGIN) : end].strip("\n") + "\n"


def apply_block(text: str, block: str) -> str:
    """Replace the managed block, or append it; text outside the markers is kept."""
    managed = f"{BLOCK_BEGIN}\n{block.strip(chr(10))}\n{BLOCK_END}"
    start = text.find(BLOCK_BEGIN)
    end = text.find(BLOCK_END)
    if start != -1 and end > start:
        return text[:start] + managed + text[end + len(BLOCK_END) :]
    if not text.strip():
        return managed + "\n"
    return text.rstrip("\n") + "\n\n" + managed + "\n"


def add_mode_arguments(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print the plan only.")
    mode.add_argument("--write", action="store_true", help="Write the result.")


def merge_settings_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack merge-settings",
        description=(
            "Deep-merge a JSON fragment into a JSON file: objects by key, arrays as "
            "unions, mstack's scalars win, other keys untouched. Prints the changes."
        ),
    )
    parser.add_argument("fragment", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument(
        "--under",
        action="append",
        default=[],
        help="Nest the fragment under this key first (repeat for a path).",
    )
    add_mode_arguments(parser)
    arguments = parser.parse_args(argv)
    target = arguments.target.expanduser()
    try:
        fragment = nest(load_json_object(arguments.fragment), arguments.under)
        merged, changes = deep_merge(
            load_json_object(target, missing_ok=True), fragment
        )
    except MergeError as error:
        logger.error("merge-settings: %s", error)
        return 1
    if arguments.write and changes:
        atomic_write_text(target, json.dumps(merged, indent=2) + "\n")
    payload = {
        "target": str(arguments.target),
        "written": bool(arguments.write and changes),
        "changes": [change.model_dump() for change in changes],
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def merge_block_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack merge-block",
        description=(
            f"Put a file's text between {BLOCK_BEGIN} and {BLOCK_END} in the target, "
            "replacing only that block. Prints whether it changes."
        ),
    )
    parser.add_argument("block", type=Path)
    parser.add_argument("target", type=Path)
    add_mode_arguments(parser)
    arguments = parser.parse_args(argv)
    target = arguments.target.expanduser()
    try:
        block = arguments.block.read_text(encoding="utf-8")
        current = target.read_text(encoding="utf-8") if target.exists() else ""
    except OSError as error:
        logger.error("merge-block: %s", error)
        return 1
    updated = apply_block(current, block)
    changed = updated != current
    if arguments.write and changed:
        atomic_write_text(target, updated)
    payload = {
        "target": str(arguments.target),
        "changed": changed,
        "written": bool(arguments.write and changed),
    }
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0
