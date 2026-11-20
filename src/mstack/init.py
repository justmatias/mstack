"""`mstack init`: scaffold the rules-as-checks layout in any repo.

It shows every file it would write and waits for confirmation. It never overwrites
a file: it creates missing ones, and appends to `.pre-commit-config.yaml` and the
`Makefile` only when the mstack entries are not there yet, so a second run changes
nothing.
"""

import argparse
import importlib.metadata
import importlib.resources
import logging
import re
import sys
from pathlib import Path
from typing import Literal

import yaml

from mstack import lint
from mstack.config import StrictModel, find_config_file, find_git_root

logger = logging.getLogger(__name__)

Action = Literal["create", "append", "exists, skipped"]
MSTACK_REPOSITORY = "https://github.com/justmatias/mstack"
PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
WORKFLOW = Path(".github/workflows/mstack.yml")
MAKEFILE_TARGET = re.compile(r"^(?P<target>[A-Za-z0-9_.-]+)\s*:(?!=)", re.MULTILINE)
TOP_LEVEL_KEY = re.compile(r"^[^\s#-][^:]*:")
LIST_ITEM = re.compile(r"^(?P<indent>\s*)-\s")


class InitError(Exception):
    pass


class PlannedFile(StrictModel):
    path: Path
    action: Action
    # The file's full content after the change; empty when skipped.
    content: str = ""


def mstack_version() -> str:
    return importlib.metadata.version("mstack")


def template(name: str, **values: str) -> str:
    text = (
        importlib.resources
        .files("mstack")
        .joinpath("templates", name)
        .read_text(encoding="utf-8")
    )
    for key, value in values.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text


def create(path: Path, content: str) -> PlannedFile:
    if path.exists():
        return PlannedFile(path=path, action="exists, skipped")
    return PlannedFile(path=path, action="create", content=content)


def plan_layout(root: Path, rules_dir: str, checks_dir: str) -> list[PlannedFile]:
    values = {"rules_dir": rules_dir, "checks_dir": checks_dir}
    checks = root / checks_dir
    rules = root / rules_dir
    return [
        create(root / ".mstack.toml", template("mstack.toml", **values)),
        create(checks / "sgconfig.yml", template("sgconfig.yml")),
        create(checks / "rules" / ".gitkeep", ""),
        create(checks / "rule-tests" / ".gitkeep", ""),
        create(rules / ".gitkeep", "")
        if not rules.is_dir()
        else PlannedFile(path=rules, action="exists, skipped"),
    ]


def repos_insertion_point(lines: list[str]) -> tuple[int, str]:
    """Where the mstack entry goes in `repos:` and the indent its items use."""
    start = next(
        (index for index, line in enumerate(lines) if re.match(r"^repos:\s*$", line)),
        None,
    )
    if start is None:
        raise InitError(f"{PRE_COMMIT_CONFIG} has no top-level 'repos:' list")
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if TOP_LEVEL_KEY.match(lines[index])
        ),
        len(lines),
    )
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    indent = next(
        (
            match["indent"]
            for line in lines[start + 1 : end]
            if (match := LIST_ITEM.match(line))
        ),
        "  ",
    )
    return end, indent


def append_pre_commit_entry(text: str, entry: str) -> str:
    lines = text.splitlines()
    end, indent = repos_insertion_point(lines)
    block = [f"{indent}{line}" if line else line for line in entry.splitlines()]
    updated = "\n".join([*lines[:end], *block, *lines[end:]]) + "\n"
    before = (yaml.safe_load(text) or {}).get("repos") or []
    after = (yaml.safe_load(updated) or {}).get("repos") or []
    if len(after) != len(before) + 1 or after[: len(before)] != before:
        raise InitError(f"could not append the mstack hooks to {PRE_COMMIT_CONFIG}")
    return updated


def plan_pre_commit(root: Path, version: str) -> PlannedFile:
    path = root / PRE_COMMIT_CONFIG
    entry = template("pre-commit.yaml", version=version)
    if not path.is_file():
        indented = "".join(f"  {line}\n" for line in entry.splitlines())
        return PlannedFile(path=path, action="create", content=f"repos:\n{indented}")
    text = path.read_text(encoding="utf-8")
    if MSTACK_REPOSITORY in text:
        return PlannedFile(path=path, action="exists, skipped")
    return PlannedFile(
        path=path, action="append", content=append_pre_commit_entry(text, entry)
    )


def plan_workflow(root: Path, version: str) -> PlannedFile:
    return create(root / WORKFLOW, template("workflow.yml", version=version))


def makefile_blocks() -> dict[str, str]:
    """The snippet's blocks (separated by blank lines), by the target they define."""
    blocks = template("Makefile.snippet").strip().split("\n\n")
    return {
        match["target"]: block
        for block in blocks
        if (match := MAKEFILE_TARGET.search(block.replace(".PHONY:", "")))
    }


def plan_makefile(root: Path) -> PlannedFile:
    path = root / "Makefile"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    defined = {match["target"] for match in MAKEFILE_TARGET.finditer(text)}
    missing = [
        block for target, block in makefile_blocks().items() if target not in defined
    ]
    if not missing:
        return PlannedFile(path=path, action="exists, skipped")
    separator = "\n" if text and not text.endswith("\n") else ""
    prefix = f"{text}{separator}\n" if text else ""
    return PlannedFile(
        path=path,
        action="append" if text else "create",
        content=prefix + "\n\n".join(missing) + "\n",
    )


def existing_layout(root: Path) -> Path | None:
    found = find_config_file(root, find_git_root(root))
    if found:
        return found[0]
    default_sgconfig = root / "lint-rules" / "sgconfig.yml"
    return default_sgconfig if default_sgconfig.is_file() else None


def build_plan(root: Path, arguments: argparse.Namespace) -> list[PlannedFile]:
    plan: list[PlannedFile] = []
    if existing := existing_layout(root):
        logger.info(
            "init: %s already exists; the layout is left as it is, only missing "
            "optional pieces are added",
            existing.relative_to(root),
        )
    else:
        plan.extend(plan_layout(root, arguments.rules_dir, arguments.checks_dir))
    version = mstack_version()
    if arguments.pre_commit:
        plan.append(plan_pre_commit(root, version))
    if arguments.ci == "github":
        plan.append(plan_workflow(root, version))
    if arguments.makefile:
        plan.append(plan_makefile(root))
    return plan


def show_plan(plan: list[PlannedFile], root: Path) -> None:
    for planned in plan:
        logger.info("  %-16s %s", planned.action, planned.path.relative_to(root))


def confirmed() -> bool:
    sys.stderr.write("Write these files? [y/N] ")
    sys.stderr.flush()
    return sys.stdin.readline().strip().lower() in {"y", "yes"}


def write_plan(plan: list[PlannedFile]) -> None:
    for planned in plan:
        if planned.action == "exists, skipped":
            continue
        planned.path.parent.mkdir(parents=True, exist_ok=True)
        planned.path.write_text(planned.content, encoding="utf-8")


def relative_folder(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise argparse.ArgumentTypeError(f"'{value}' must be a folder inside the repo")
    return path.as_posix()


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mstack init",
        description=(
            "Scaffold the rules-as-checks layout: .mstack.toml, an ast-grep "
            "sgconfig with empty rules/ and rule-tests/, and the rules folder. "
            "Shows the plan and waits for confirmation; never overwrites a file."
        ),
    )
    parser.add_argument("--rules-dir", type=relative_folder, default=".cursor/rules")
    parser.add_argument("--checks-dir", type=relative_folder, default="lint-rules")
    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help=f"Add the mstack hooks to {PRE_COMMIT_CONFIG}, pinned to this version.",
    )
    parser.add_argument(
        "--ci",
        choices=["github"],
        help=f"Write {WORKFLOW.as_posix()}, which runs the mstack action.",
    )
    parser.add_argument(
        "--makefile",
        action="store_true",
        help="Add lint-rules and lint-rules-changed targets to the Makefile.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the plan and write nothing."
    )
    parser.add_argument(
        "--yes", action="store_true", help="Write without asking for confirmation."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    current_directory = Path.cwd().resolve()
    root = find_git_root(current_directory) or current_directory
    try:
        plan = build_plan(root, arguments)
    except InitError as error:
        logger.error("mstack init: %s", error)
        return 2
    logger.info("init: plan for %s", root)
    show_plan(plan, root)
    if all(planned.action == "exists, skipped" for planned in plan):
        logger.info("init: nothing to write")
        return 0
    if arguments.dry_run:
        logger.info("init: dry run, nothing written")
        return 0
    if not arguments.yes and not confirmed():
        logger.info("init: nothing written")
        return 1
    write_plan(plan)
    logger.info("init: done; running mstack lint on the new layout")
    return lint.main([])
