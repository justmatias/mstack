import argparse
import datetime
import importlib.metadata
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from mstack.install.files import atomic_write_text
from mstack.install.item_kinds import (
    KINDS,
    Kind,
    SourceError,
    SourceItem,
    Tool,
    expand,
    installed_hash,
    owns_target,
    source_hash,
    source_items,
    written_keys,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
MANIFEST_NAME = "manifest.json"

ACTIONS = {
    "new": "add",
    "identical": "none",
    "unknown": "ask",
    "upstream-changed": "update (back up first)",
    "locally-edited": "keep, and tell the user",
    "conflict": "ask: update, keep or combine",
    "removed": "ask: reinstall or forget",
    "orphan": "ask: uninstall or keep",
    "old-symlink": "replace with a copy",
}

# (locally edited, upstream changed) -> state, for an item with a record.
STATE_BY_CHANGES = {
    (False, False): "identical",
    (True, False): "locally-edited",
    (False, True): "upstream-changed",
    (True, True): "conflict",
}


class ManifestError(Exception):
    """The manifest cannot be read, written or understood."""


class ManifestItem(BaseModel):
    kind: Kind
    name: str
    target: str
    hash: str
    # The source hash at install time. It differs from `hash` only for an item the
    # user combined, so a combined item is not reported as upstream-changed forever.
    source_hash: str
    source_version: str | None
    source_commit: str | None
    installed_at: str
    # For merged items (mcp, settings): the JSON keys mstack wrote.
    keys: list[str] | None = None


class Manifest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: int = Field(default=SCHEMA_VERSION, alias="schema")
    items: list[ManifestItem] = []

    def find(self, kind: str, name: str, target: Path) -> ManifestItem | None:
        for item in self.items:
            if (
                item.kind == kind
                and item.name == name
                and expand(item.target) == target
            ):
                return item
        return None


class ItemStatus(BaseModel):
    kind: Kind
    name: str
    target: str
    state: str
    action: str
    recorded: bool


def state_directory() -> Path:
    if sys.platform == "win32" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "mstack"
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "mstack"


def manifest_path() -> Path:
    return state_directory() / MANIFEST_NAME


def abbreviate(target: Path) -> str:
    home = Path.home()
    if target.is_relative_to(home):
        return "~/" + target.relative_to(home).as_posix()
    return str(target)


def load_manifest(path: Path) -> Manifest:
    if not path.exists():
        return Manifest()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"cannot read {path}: {error}") from error
    schema = data.get("schema") if isinstance(data, dict) else None
    if schema != SCHEMA_VERSION:
        raise ManifestError(
            f"{path} has schema {schema!r}, but this mstack only reads schema "
            f"{SCHEMA_VERSION}; update mstack or move the file away"
        )
    try:
        return Manifest.model_validate(data)
    except ValidationError as error:
        raise ManifestError(f"{path} is malformed: {error}") from error


def save_manifest(manifest: Manifest, path: Path) -> None:
    atomic_write_text(path, manifest.model_dump_json(by_alias=True, indent=2) + "\n")


def item_state(
    source_hash: str, record: ManifestItem | None, installed_hash: str | None
) -> str:
    if record is None:
        if installed_hash is None:
            return "new"
        return "identical" if installed_hash == source_hash else "unknown"
    if installed_hash is None:
        return "removed"
    changes = (installed_hash != record.hash, source_hash != record.source_hash)
    return STATE_BY_CHANGES[changes]


def status_row(
    kind: Kind, name: str, target: Path, state: str, *, recorded: bool
) -> ItemStatus:
    action = ACTIONS[state] if recorded or state != "identical" else "record it"
    return ItemStatus(
        kind=kind,
        name=name,
        target=abbreviate(target),
        state=state,
        action=action,
        recorded=recorded,
    )


def orphan_rows(
    manifest: Manifest, sources: list[SourceItem], tool: Tool
) -> list[ItemStatus]:
    known = {(source.kind, source.name, source.target) for source in sources}
    return [
        status_row(
            record.kind, record.name, expand(record.target), "orphan", recorded=True
        )
        for record in manifest.items
        if owns_target(record.kind, expand(record.target), tool)
        and (record.kind, record.name, expand(record.target)) not in known
    ]


def compute_status(checkout: Path, tool: Tool, manifest: Manifest) -> list[ItemStatus]:
    try:
        sources = source_items(checkout, tool)
    except SourceError as error:
        raise ManifestError(str(error)) from error
    rows: list[ItemStatus] = []
    for source in sources:
        record = manifest.find(source.kind, source.name, source.target)
        if source.target.is_symlink():
            state = "old-symlink"
        else:
            try:
                installed = installed_hash(
                    checkout, source.kind, source.name, source.target
                )
            except SourceError as error:
                raise ManifestError(str(error)) from error
            state = item_state(source.source_hash, record, installed)
        rows.append(
            status_row(
                source.kind,
                source.name,
                source.target,
                state,
                recorded=record is not None,
            )
        )
    return rows + orphan_rows(manifest, sources, tool)


def source_commit(checkout: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = completed.stdout.strip()
    return commit if completed.returncode == 0 and len(commit) == 40 else None


def source_version() -> str | None:
    try:
        return importlib.metadata.version("mstack")
    except importlib.metadata.PackageNotFoundError:
        return None


def record_item(
    manifest: Manifest, kind: Kind, name: str, target: Path, checkout: Path
) -> ManifestItem:
    try:
        installed = installed_hash(checkout, kind, name, target)
        source = source_hash(checkout, kind, name)
        keys = written_keys(checkout, kind, name)
    except SourceError as error:
        raise ManifestError(str(error)) from error
    if installed is None:
        raise ManifestError(f"nothing is installed at {target} for {kind} {name}")
    item = ManifestItem(
        kind=kind,
        name=name,
        target=abbreviate(target),
        hash=installed,
        source_hash=source,
        keys=keys,
        source_version=source_version(),
        source_commit=source_commit(checkout),
        installed_at=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    forget_items(manifest, kind, name, target)
    manifest.items.append(item)
    return item


def forget_items(
    manifest: Manifest, kind: str, name: str, target: Path | None = None
) -> int:
    kept = [
        item
        for item in manifest.items
        if not (
            item.kind == kind
            and item.name == name
            and (target is None or expand(item.target) == target)
        )
    ]
    removed = len(manifest.items) - len(kept)
    manifest.items = kept
    return removed


def run_status(arguments: argparse.Namespace, manifest: Manifest) -> int:
    rows = compute_status(arguments.checkout, arguments.tool, manifest)
    if arguments.json:
        payload = {"items": [row.model_dump() for row in rows]}
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0
    for row in rows:
        sys.stdout.write(
            f"{row.state:<20} {row.kind:<5} {row.name:<28} {row.target}"
            f"  ({row.action})\n"
        )
    return 0


def run_record(arguments: argparse.Namespace, manifest: Manifest) -> int:
    item = record_item(
        manifest,
        arguments.kind,
        arguments.name,
        expand(arguments.target),
        arguments.checkout,
    )
    save_manifest(manifest, manifest_path())
    logger.info("manifest: recorded %s %s at %s", item.kind, item.name, item.target)
    return 0


def run_forget(arguments: argparse.Namespace, manifest: Manifest) -> int:
    target = expand(arguments.target) if arguments.target else None
    removed = forget_items(manifest, arguments.kind, arguments.name, target)
    if not removed:
        logger.info("manifest: no record of %s %s", arguments.kind, arguments.name)
        return 0
    save_manifest(manifest, manifest_path())
    logger.info("manifest: forgot %d record(s)", removed)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mstack manifest",
        description=(
            f"Track what mstack installed and its content hash ({manifest_path()})."
        ),
    )
    commands = parser.add_subparsers(dest="action", required=True)

    status = commands.add_parser(
        "status", help="State of every skill and rule in the checkout."
    )
    status.add_argument("--tool", choices=["claude", "cursor", "both"], required=True)
    status.add_argument("--json", action="store_true", help="Print JSON.")
    status.set_defaults(handler=run_status)

    record = commands.add_parser(
        "record", help="Record the installed hash of an item after installing it."
    )
    record.add_argument("kind", choices=KINDS)
    record.add_argument("name")
    record.add_argument("target", help="Where the item was installed.")
    record.set_defaults(handler=run_record)

    forget = commands.add_parser("forget", help="Drop an item's record.")
    forget.add_argument("kind", choices=KINDS)
    forget.add_argument("name")
    forget.add_argument(
        "--target", help="Only the record for this target (default: every one)."
    )
    forget.set_defaults(handler=run_forget)

    for subparser in (status, record):
        subparser.add_argument(
            "--checkout",
            type=Path,
            default=Path.cwd(),
            help="The mstack checkout (default: the current folder).",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        manifest = load_manifest(manifest_path())
        exit_code: int = arguments.handler(arguments, manifest)
    except ManifestError as error:
        logger.error("manifest: %s", error)
        return 1
    return exit_code
