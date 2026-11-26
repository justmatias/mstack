import argparse
import logging
import shutil
import stat
import sys
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mstack.platform import codex_folder, run_quiet, tool_homes

logger = logging.getLogger(__name__)
BACKUP_FOLDER = ".mstack-backups"
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
RETENTION = timedelta(days=30)


def plain_directory(path: Path) -> bool:
    return not (path.is_symlink() or path.is_junction()) and path.is_dir()


def user_folders() -> Iterator[Path]:
    homes = tool_homes()
    claude = homes["claude"] / ".claude"
    cursor = homes["cursor"] / ".cursor"
    codex = codex_folder(homes["claude"])
    for folder in (claude, cursor, codex):
        if plain_directory(folder):
            yield folder
            yield from (folder / name for name in ("agents", "skills", "rules"))
    agents = homes["claude"] / ".agents"
    if plain_directory(agents):
        yield agents / "skills"
    for options in ([], ["--bin"]):
        if location := run_quiet(["uv", "tool", "dir", *options]):
            yield Path(location)


def checkout_folders(checkout: Path) -> Iterator[Path]:
    yield checkout / "rules"
    yield checkout
    skills = checkout / "skills"
    if plain_directory(skills):
        yield skills
        yield from (
            group for group in skills.iterdir() if not group.name.startswith(".")
        )


def backup_timestamp(name: str) -> datetime | None:
    try:
        timestamp = datetime.strptime(name, TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None
    return timestamp if timestamp.strftime(TIMESTAMP_FORMAT) == name else None


def old_batches(root: Path, cutoff: datetime) -> Iterator[Path]:
    batches = []
    for batch in root.iterdir():
        if plain_directory(batch) and (timestamp := backup_timestamp(batch.name)):
            batches.append((timestamp, batch))
    for timestamp, batch in sorted(batches, reverse=True)[1:]:
        if timestamp < cutoff:
            yield batch


def directory_size(folder: Path) -> int:
    total = 0
    for parent, directories, files in folder.walk():
        directories[:] = [
            name for name in directories if not (parent / name).is_junction()
        ]
        for name in files:
            entry = (parent / name).lstat()
            if stat.S_ISREG(entry.st_mode):
                total += entry.st_size
    return total


def cleanup_candidates(checkout: Path | None, cutoff: datetime) -> Iterator[Path]:
    folders = set(user_folders())
    if checkout is not None:
        folders.update(checkout_folders(checkout))
    roots = {
        root.resolve()
        for folder in folders
        if plain_directory(folder) and plain_directory(root := folder / BACKUP_FOLDER)
    }
    for root in sorted(roots):
        yield from old_batches(root, cutoff)


def main(argv: list[str] | None = None, *, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack cleanup",
        description="Preview mstack backups older than 30 days, keeping the newest in each folder.",
    )
    parser.add_argument("--apply", action="store_true", help="Delete eligible backups.")
    parser.add_argument(
        "--checkout", type=Path, help="Also scan backups in this checkout."
    )
    arguments = parser.parse_args(argv)
    checkout = arguments.checkout
    if checkout is not None:
        try:
            checkout = checkout.expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as error:
            parser.error(f"invalid --checkout: {error}")
        if not checkout.is_dir():
            parser.error("--checkout must be an existing directory")
    cutoff = (now or datetime.now(UTC)) - RETENTION
    try:
        candidates = [
            (path, directory_size(path))
            for path in cleanup_candidates(checkout, cutoff)
        ]
        action = "Removed" if arguments.apply else "Would remove"
        for path, size in candidates:
            if arguments.apply:
                if path.resolve() != path or not plain_directory(path):
                    raise OSError(f"backup path changed: {path}")
                shutil.rmtree(path)
            sys.stdout.write(f"{action} {path} ({size:,} bytes)\n")
    except (OSError, RuntimeError) as error:
        logger.error("cleanup: %s", error)
        return 1
    total = sum(size for _, size in candidates)
    action = "Removed" if arguments.apply else "Eligible"
    sys.stdout.write(f"{action}: {len(candidates)} backup batches, {total:,} bytes.\n")
    return 0
