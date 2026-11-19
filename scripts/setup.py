#!/usr/bin/env python3
import argparse
import datetime
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("setup")

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SOURCE = REPOSITORY_ROOT / "skills"
COMPONENTS = {
    "pre-commit": "pre-commit hook: static checks and `make lint-rules-changed` on staged files",
    "claude-hook": "Claude Code PostToolUse hook that scans every edited .py file",
    "cursor-hook": "Cursor postToolUse hook that scans every edited .py file",
    "skills": "symlink sync-rules, reflect-rules and correct-rules into the agents' skill folders",
}
CLAUDE_HOOK_COMMAND = '"$CLAUDE_PROJECT_DIR"/scripts/hooks/claude_post_edit.sh'
CLAUDE_HOOK_MATCHER = "Edit|Write"
CURSOR_HOOK_COMMAND = "scripts/hooks/cursor_after_edit.sh"
CURSOR_HOOK_MATCHER = "Write"


class Installer:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    @staticmethod
    def read_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def write_json(self, path: Path, data: dict, original: dict) -> None:
        if data == original:
            logger.info("unchanged: %s", path)
            return
        if self.dry_run:
            logger.info("would update: %s", path)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            backup = path.with_name(f"{path.name}.bak-{self.timestamp}")
            shutil.copy2(path, backup)
            logger.info("backup: %s", backup)
        if not data.get("hooks") and set(data) <= {"hooks", "version"}:
            path.unlink(missing_ok=True)
            logger.info("removed (nothing left): %s", path)
            return
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        logger.info("updated: %s", path)

    def run(self, *command: str) -> None:
        if self.dry_run:
            logger.info("would run: %s", " ".join(command))
            return
        subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)

    def link(self, link: Path, target: Path) -> None:
        if link.is_symlink() and link.resolve() == target.resolve():
            logger.info("unchanged: %s", link)
            return
        if link.exists() or link.is_symlink():
            logger.warning("skipped: %s already exists and is not our symlink", link)
            return
        if self.dry_run:
            logger.info("would link: %s -> %s", link, target)
            return
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        logger.info("linked: %s -> %s", link, target)

    def unlink(self, link: Path, target: Path) -> None:
        if not (link.is_symlink() and link.resolve() == target.resolve()):
            return
        if self.dry_run:
            logger.info("would remove: %s", link)
            return
        link.unlink()
        logger.info("removed: %s", link)


def claude_settings_path(scope: str) -> Path:
    name = "settings.json" if scope == "project" else "settings.local.json"
    return REPOSITORY_ROOT / ".claude" / name


def skills_directories(scope: str) -> list[Path]:
    base = Path.home() if scope == "global" else REPOSITORY_ROOT
    return [base / ".claude" / "skills", base / ".cursor" / "skills"]


def has_hook(entries: list, command: str) -> bool:
    return any(
        command == hook.get("command")
        for entry in entries
        for hook in (entry, *entry.get("hooks", []))
    )


def install_claude_hook(installer: Installer, scope: str) -> None:
    path = claude_settings_path(scope)
    original = installer.read_json(path)
    settings = json.loads(json.dumps(original))
    entries = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    if not has_hook(entries, CLAUDE_HOOK_COMMAND):
        entries.append({
            "matcher": CLAUDE_HOOK_MATCHER,
            "hooks": [{"type": "command", "command": CLAUDE_HOOK_COMMAND}],
        })
    installer.write_json(path, settings, original)


def uninstall_claude_hook(installer: Installer, scope: str) -> None:
    path = claude_settings_path(scope)
    original = installer.read_json(path)
    settings = json.loads(json.dumps(original))
    hooks = settings.get("hooks", {})
    remaining = []
    for entry in hooks.get("PostToolUse", []):
        entry["hooks"] = [
            hook
            for hook in entry.get("hooks", [])
            if hook.get("command") != CLAUDE_HOOK_COMMAND
        ]
        if entry["hooks"]:
            remaining.append(entry)
    if "PostToolUse" in hooks:
        hooks["PostToolUse"] = remaining
        if not remaining:
            del hooks["PostToolUse"]
        if not hooks:
            del settings["hooks"]
    installer.write_json(path, settings, original)


def install_cursor_hook(installer: Installer) -> None:
    path = REPOSITORY_ROOT / ".cursor" / "hooks.json"
    original = installer.read_json(path)
    config = json.loads(json.dumps(original))
    config.setdefault("version", 1)
    entries = config.setdefault("hooks", {}).setdefault("postToolUse", [])
    if not has_hook(entries, CURSOR_HOOK_COMMAND):
        entries.append({"command": CURSOR_HOOK_COMMAND, "matcher": CURSOR_HOOK_MATCHER})
    installer.write_json(path, config, original)


def uninstall_cursor_hook(installer: Installer) -> None:
    path = REPOSITORY_ROOT / ".cursor" / "hooks.json"
    original = installer.read_json(path)
    config = json.loads(json.dumps(original))
    hooks = config.get("hooks", {})
    if "postToolUse" in hooks:
        hooks["postToolUse"] = [
            entry
            for entry in hooks["postToolUse"]
            if entry.get("command") != CURSOR_HOOK_COMMAND
        ]
        if not hooks["postToolUse"]:
            del hooks["postToolUse"]
    installer.write_json(path, config, original)


def skill_sources() -> list[Path]:
    return sorted(
        path for path in SKILLS_SOURCE.glob("*") if (path / "SKILL.md").is_file()
    )


def install_skills(installer: Installer, scope: str) -> None:
    sources = skill_sources()
    if not sources:
        logger.warning("no skills found in %s", SKILLS_SOURCE)
    for directory in skills_directories(scope):
        for source in sources:
            installer.link(directory / source.name, source)


def uninstall_skills(installer: Installer, scope: str) -> None:
    for directory in skills_directories(scope):
        for source in skill_sources():
            installer.unlink(directory / source.name, source)


def ask(question: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{question} {suffix} ").strip().lower()
    return default if not answer else answer in {"y", "yes"}


def choose(question: str, options: list[str]) -> str:
    answer = (
        input(f"{question} ({'/'.join(options)}, default {options[0]}) ")
        .strip()
        .lower()
    )
    return answer if answer in options else options[0]


def resolve_choices(arguments: argparse.Namespace) -> set[str]:
    if arguments.with_components:
        return set(arguments.with_components) - set(arguments.without_components)
    selected = set(COMPONENTS) - set(arguments.without_components)
    if arguments.yes or not sys.stdin.isatty():
        return selected
    chosen = {
        name
        for name, description in COMPONENTS.items()
        if name in selected and ask(f"Install the {name}: {description}?")
    }
    if "claude-hook" in chosen and not arguments.claude_settings_given:
        arguments.claude_settings = choose(
            "Claude Code hook in settings.local.json (only you) or settings.json (whole team)?",
            ["local", "project"],
        )
    if "skills" in chosen and not arguments.skills_scope_given:
        arguments.skills_scope = choose(
            "Install skills for this repo or for every repo?", ["project", "global"]
        )
    return chosen


def project_command(arguments: argparse.Namespace) -> int:
    installer = Installer(arguments.dry_run)
    components = resolve_choices(arguments)
    action = "uninstall" if arguments.uninstall else "install"
    logger.info("%s: %s", action, ", ".join(sorted(components)) or "nothing")
    if "pre-commit" in components:
        installer.run("uv", "run", "pre-commit", action)
    if "claude-hook" in components:
        (uninstall_claude_hook if arguments.uninstall else install_claude_hook)(
            installer, arguments.claude_settings
        )
    if "cursor-hook" in components:
        (uninstall_cursor_hook if arguments.uninstall else install_cursor_hook)(
            installer
        )
    if "skills" in components:
        (uninstall_skills if arguments.uninstall else install_skills)(
            installer, arguments.skills_scope
        )
    return 0


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="setup.py",
        description=(
            "Install the mstack integrations you want. Asks interactively unless "
            "flags are given."
        ),
    )
    subcommands = parser.add_subparsers(dest="command")
    project = subcommands.add_parser(
        "project", help="Integrations for this repo (default)."
    )
    for subparser in (project,):
        subparser.add_argument(
            "--with",
            dest="with_components",
            action="append",
            choices=sorted(COMPONENTS),
            default=[],
            help="Only these components (repeatable). Skips the questions.",
        )
        subparser.add_argument(
            "--without",
            dest="without_components",
            action="append",
            choices=sorted(COMPONENTS),
            default=[],
            help="Every component except these (repeatable).",
        )
        subparser.add_argument(
            "--claude-settings", choices=["local", "project"], default=None
        )
        subparser.add_argument(
            "--skills-scope", choices=["project", "global"], default=None
        )
        subparser.add_argument(
            "--yes",
            "-y",
            action="store_true",
            help="Accept the defaults without asking.",
        )
        subparser.add_argument(
            "--uninstall", action="store_true", help="Remove what install adds."
        )
        subparser.add_argument(
            "--dry-run", action="store_true", help="Show what would change."
        )
    if (
        not argv
        or argv[0] not in subcommands.choices
        and argv[0] not in {"-h", "--help"}
    ):
        argv = ["project", *argv]
    arguments = parser.parse_args(argv)
    arguments.claude_settings_given = arguments.claude_settings is not None
    arguments.skills_scope_given = arguments.skills_scope is not None
    arguments.claude_settings = arguments.claude_settings or "local"
    arguments.skills_scope = arguments.skills_scope or "project"
    return arguments


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="setup: %(message)s")
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    return project_command(arguments)


if __name__ == "__main__":
    sys.exit(main())
