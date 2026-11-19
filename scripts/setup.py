#!/usr/bin/env python3
import argparse
import datetime
import json
import logging
import os
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
USER_COMPONENTS = {
    "rules": (
        "copy the personal rule set to $MY_RULES_HOME (never overwrites) and its "
        "prose rules to ~/.cursor/rules"
    ),
    "claude-hook": "Claude Code PostToolUse hook in ~/.claude/settings.json, in every repo",
    "cursor-hook": "Cursor postToolUse hook in ~/.cursor/hooks.json, in every repo",
    "git-hooks": (
        "global core.hooksPath that runs the personal set on commit and chains to "
        "each repo's hooks"
    ),
    "skills": "symlink the three skills into ~/.claude/skills and ~/.cursor/skills",
}
USER_TEMPLATE = REPOSITORY_ROOT / "user-level"
GIT_HOOK_NAMES = [
    "applypatch-msg",
    "pre-applypatch",
    "post-applypatch",
    "pre-commit",
    "pre-merge-commit",
    "prepare-commit-msg",
    "commit-msg",
    "post-commit",
    "pre-rebase",
    "post-checkout",
    "post-merge",
    "pre-push",
    "pre-receive",
    "update",
    "proc-receive",
    "post-receive",
    "post-update",
    "reference-transaction",
    "push-to-checkout",
    "pre-auto-gc",
    "post-rewrite",
    "sendemail-validate",
    "fsmonitor-watchman",
    "p4-changelist",
    "p4-prepare-changelist",
    "p4-post-changelist",
    "p4-pre-submit",
    "post-index-change",
]
CLAUDE_HOOK_COMMAND = '"$CLAUDE_PROJECT_DIR"/scripts/hooks/claude_post_edit.sh'
# MultiEdit is gone from current Claude Code, but older versions still send it.
CLAUDE_HOOK_MATCHER = "Edit|Write|MultiEdit"
CURSOR_HOOK_COMMAND = "scripts/hooks/cursor_after_edit.sh"
# The Cursor hook has no matcher: Cursor does not document which tools edit files,
# so the hook runs after every tool and acts only when the input names a .py file.


class Installer:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

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
        for backup in sorted(path.parent.glob(f"{path.name}.bak-*")):
            try:
                if json.loads(backup.read_text(encoding="utf-8")) == data:
                    path.write_bytes(backup.read_bytes())
                    logger.info(
                        "restored the original bytes of %s from %s", path, backup
                    )
                    return
            except ValueError:
                continue
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


def entries_with_hook(entries: list, command: str) -> list[dict]:
    return [
        entry
        for entry in entries
        if any(
            command == hook.get("command") for hook in (entry, *entry.get("hooks", []))
        )
    ]


def add_claude_hook(installer: Installer, path: Path, command: str) -> None:
    original = installer.read_json(path)
    settings = json.loads(json.dumps(original))
    entries = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    ours = entries_with_hook(entries, command)
    for entry in ours:
        entry["matcher"] = CLAUDE_HOOK_MATCHER  # upgrades an older matcher
    if not ours:
        entries.append({
            "matcher": CLAUDE_HOOK_MATCHER,
            "hooks": [{"type": "command", "command": command}],
        })
    installer.write_json(path, settings, original)


def remove_claude_hook(installer: Installer, path: Path, command: str) -> None:
    original = installer.read_json(path)
    settings = json.loads(json.dumps(original))
    hooks = settings.get("hooks", {})
    if "PostToolUse" in hooks:
        remaining = []
        for entry in hooks["PostToolUse"]:
            entry["hooks"] = [
                hook
                for hook in entry.get("hooks", [])
                if hook.get("command") != command
            ]
            if entry["hooks"]:
                remaining.append(entry)
        hooks["PostToolUse"] = remaining
        if not remaining:
            del hooks["PostToolUse"]
        if not hooks:
            del settings["hooks"]
    installer.write_json(path, settings, original)


def add_cursor_hook(installer: Installer, path: Path, command: str) -> None:
    original = installer.read_json(path)
    config = json.loads(json.dumps(original))
    config.setdefault("version", 1)
    entries = config.setdefault("hooks", {}).setdefault("postToolUse", [])
    ours = entries_with_hook(entries, command)
    for entry in ours:
        entry.pop("matcher", None)  # an older install matched Write only
    if not ours:
        entries.append({"command": command})
    installer.write_json(path, config, original)


def remove_cursor_hook(installer: Installer, path: Path, command: str) -> None:
    original = installer.read_json(path)
    config = json.loads(json.dumps(original))
    hooks = config.get("hooks", {})
    if "postToolUse" in hooks:
        hooks["postToolUse"] = [
            entry for entry in hooks["postToolUse"] if entry.get("command") != command
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


def resolve_choices(
    arguments: argparse.Namespace, components: dict[str, str]
) -> set[str]:
    if arguments.with_components:
        return set(arguments.with_components) - set(arguments.without_components)
    selected = set(components) - set(arguments.without_components)
    if arguments.yes or not sys.stdin.isatty():
        return selected
    verb = "Uninstall" if arguments.uninstall else "Install"
    chosen = {
        name
        for name, description in components.items()
        if name in selected and ask(f"{verb} the {name}: {description}?")
    }
    if arguments.command == "user":
        return chosen
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
    components = resolve_choices(arguments, COMPONENTS)
    action = "uninstall" if arguments.uninstall else "install"
    logger.info("%s: %s", action, ", ".join(sorted(components)) or "nothing")
    if "pre-commit" in components:
        installer.run("uv", "run", "pre-commit", action)
    if "claude-hook" in components:
        (remove_claude_hook if arguments.uninstall else add_claude_hook)(
            installer,
            claude_settings_path(arguments.claude_settings),
            CLAUDE_HOOK_COMMAND,
        )
    if "cursor-hook" in components:
        (remove_cursor_hook if arguments.uninstall else add_cursor_hook)(
            installer, REPOSITORY_ROOT / ".cursor" / "hooks.json", CURSOR_HOOK_COMMAND
        )
    if "skills" in components:
        (uninstall_skills if arguments.uninstall else install_skills)(
            installer, arguments.skills_scope
        )
    return 0


def my_rules_home() -> Path:
    return Path(os.environ.get("MY_RULES_HOME", "~/.config/my-rules")).expanduser()


def template_files() -> list[Path]:
    return sorted(
        path.relative_to(USER_TEMPLATE)
        for path in USER_TEMPLATE.rglob("*")
        if path.is_file()
        and "cursor-rules" not in path.relative_to(USER_TEMPLATE).parts
    )


def install_personal_rules(installer: Installer, home: Path) -> None:
    if home.exists():
        logger.info("unchanged: %s already exists (never overwritten)", home)
    elif installer.dry_run:
        logger.info("would copy: %s -> %s", USER_TEMPLATE, home)
    else:
        for relative in template_files():
            target = home / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(USER_TEMPLATE / relative, target)
        logger.info("copied: %s -> %s", USER_TEMPLATE, home)
    for name in GIT_HOOK_NAMES:
        installer.link(home / "githooks" / name, home / "bin" / "git-hook-chain")
    for mdc in sorted((USER_TEMPLATE / "cursor-rules").glob("*.mdc")):
        target = Path.home() / ".cursor" / "rules" / mdc.name
        if target.exists():
            logger.info("unchanged: %s", target)
        elif installer.dry_run:
            logger.info("would copy: %s", target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mdc, target)
            logger.info("copied: %s", target)


def remove_if_unchanged(installer: Installer, installed: Path, template: Path) -> None:
    if not installed.is_file() or installed.is_symlink():
        return
    if installed.read_bytes() != template.read_bytes():
        logger.info("kept (modified by you): %s", installed)
        return
    if installer.dry_run:
        logger.info("would remove: %s", installed)
        return
    installed.unlink()
    logger.info("removed: %s", installed)


def remove_empty_directories(directory: Path) -> None:
    if not directory.is_dir():
        return
    for child in sorted(
        directory.rglob("*"), key=lambda path: len(path.parts), reverse=True
    ):
        if child.is_dir() and not any(child.iterdir()):
            child.rmdir()
    if not any(directory.iterdir()):
        directory.rmdir()


def uninstall_personal_rules(installer: Installer, home: Path) -> None:
    for name in GIT_HOOK_NAMES:
        installer.unlink(home / "githooks" / name, home / "bin" / "git-hook-chain")
    for relative in template_files():
        remove_if_unchanged(installer, home / relative, USER_TEMPLATE / relative)
    for mdc in sorted((USER_TEMPLATE / "cursor-rules").glob("*.mdc")):
        remove_if_unchanged(
            installer, Path.home() / ".cursor" / "rules" / mdc.name, mdc
        )
    if not installer.dry_run:
        remove_empty_directories(home)
        remove_empty_directories(Path.home() / ".cursor" / "rules")


def global_hooks_path() -> str | None:
    completed = subprocess.run(
        ["git", "config", "--global", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() or None


def install_git_hooks(installer: Installer, home: Path, replace: bool) -> None:
    ours = str(home / "githooks")
    current = global_hooks_path()
    if current == ours:
        logger.info("unchanged: core.hooksPath = %s", ours)
        return
    if current and not replace:
        logger.warning(
            "skipped: global core.hooksPath is already %s. Re-run with "
            "--replace-hooks-path to replace it (the previous value is restored on "
            "uninstall).",
            current,
        )
        return
    if installer.dry_run:
        logger.info("would set: git config --global core.hooksPath %s", ours)
        return
    (home / ".previous-hooks-path").write_text(current or "", encoding="utf-8")
    subprocess.run(["git", "config", "--global", "core.hooksPath", ours], check=True)
    logger.info(
        "set: git config --global core.hooksPath %s (previous: %s)",
        ours,
        current or "unset",
    )


def uninstall_git_hooks(installer: Installer, home: Path) -> None:
    ours = str(home / "githooks")
    if global_hooks_path() != ours:
        return
    previous_file = home / ".previous-hooks-path"
    previous = (
        previous_file.read_text(encoding="utf-8").strip()
        if previous_file.is_file()
        else ""
    )
    if installer.dry_run:
        logger.info("would restore core.hooksPath to %s", previous or "unset")
        return
    if previous:
        subprocess.run(
            ["git", "config", "--global", "core.hooksPath", previous], check=True
        )
    else:
        subprocess.run(
            ["git", "config", "--global", "--unset", "core.hooksPath"], check=True
        )
    previous_file.unlink(missing_ok=True)
    logger.info("restored core.hooksPath to %s", previous or "unset")


def uninstall_user_components(
    installer: Installer, components: set[str], home: Path
) -> None:
    logger.info("uninstall (user): %s", ", ".join(sorted(components)) or "nothing")
    if "git-hooks" in components:
        uninstall_git_hooks(installer, home)
    if "claude-hook" in components:
        remove_claude_hook(
            installer,
            Path.home() / ".claude" / "settings.json",
            str(home / "bin" / "claude-post-edit"),
        )
    if "cursor-hook" in components:
        remove_cursor_hook(
            installer,
            Path.home() / ".cursor" / "hooks.json",
            str(home / "bin" / "cursor-after-edit"),
        )
    if "skills" in components:
        uninstall_skills(installer, "global")
    if "rules" in components:
        uninstall_personal_rules(installer, home)


def install_user_components(
    installer: Installer, components: set[str], home: Path, replace_hooks_path: bool
) -> None:
    logger.info("install (user): %s", ", ".join(sorted(components)) or "nothing")
    if "rules" in components:
        install_personal_rules(installer, home)
    if "claude-hook" in components:
        add_claude_hook(
            installer,
            Path.home() / ".claude" / "settings.json",
            str(home / "bin" / "claude-post-edit"),
        )
    if "cursor-hook" in components:
        add_cursor_hook(
            installer,
            Path.home() / ".cursor" / "hooks.json",
            str(home / "bin" / "cursor-after-edit"),
        )
    if "git-hooks" in components:
        install_git_hooks(installer, home, replace_hooks_path)
    if "skills" in components:
        install_skills(installer, "global")


def user_command(arguments: argparse.Namespace) -> int:
    installer = Installer(arguments.dry_run)
    components = resolve_choices(arguments, USER_COMPONENTS)
    if arguments.uninstall:
        uninstall_user_components(installer, components, my_rules_home())
    else:
        install_user_components(
            installer, components, my_rules_home(), arguments.replace_hooks_path
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
    user = subcommands.add_parser(
        "user",
        help="Your personal rule set in $MY_RULES_HOME and global hooks, for every repo.",
    )
    project.add_argument(
        "--claude-settings", choices=["local", "project"], default=None
    )
    project.add_argument("--skills-scope", choices=["project", "global"], default=None)
    user.add_argument(
        "--replace-hooks-path",
        action="store_true",
        help="Replace an existing global core.hooksPath (restored on uninstall).",
    )
    for subparser, components in ((project, COMPONENTS), (user, USER_COMPONENTS)):
        subparser.add_argument(
            "--with",
            dest="with_components",
            action="append",
            choices=sorted(components),
            default=[],
            help="Only these components (repeatable). Skips the questions.",
        )
        subparser.add_argument(
            "--without",
            dest="without_components",
            action="append",
            choices=sorted(components),
            default=[],
            help="Every component except these (repeatable).",
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
    if arguments.command == "project":
        arguments.claude_settings_given = arguments.claude_settings is not None
        arguments.skills_scope_given = arguments.skills_scope is not None
        arguments.claude_settings = arguments.claude_settings or "local"
        arguments.skills_scope = arguments.skills_scope or "project"
    return arguments


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="setup: %(message)s")
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    return (
        user_command(arguments)
        if arguments.command == "user"
        else project_command(arguments)
    )


if __name__ == "__main__":
    sys.exit(main())
