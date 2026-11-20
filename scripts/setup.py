#!/usr/bin/env python3
# pylint: disable=too-many-lines
import argparse
import datetime
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger("setup")

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SOURCE = REPOSITORY_ROOT / "skills"
COMPONENTS = {
    "pre-commit": "pre-commit hook: static checks and `make lint-rules-changed` on staged files",
    "claude-hook": "Claude Code PostToolUse hook that scans every edited .py file",
    "cursor-hook": "Cursor postToolUse hook that scans every edited .py file",
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
CLAUDE_HOOK_MATCHER = "Edit|Write"
CURSOR_HOOK_COMMAND = "scripts/hooks/cursor_after_edit.sh"
CURSOR_HOOK_MATCHER = "Write"
SETUP_SKILL = "setup-mstack"
TOOLS = ("claude", "cursor")
MANIFEST_NAME = ".mstack-manifest.json"
MANIFEST_VERSION = 1
BACKUPS_NAME = ".mstack-backups"
MSTACK_PREFIX = "mstack-"
IGNORED_NAMES = frozenset({".DS_Store", "__pycache__"})
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NAME_THRESHOLD = 0.5
DESCRIPTION_THRESHOLD = 0.25
STOPWORDS = frozenset({
    "and",
    "any",
    "are",
    "but",
    "can",
    "each",
    "for",
    "from",
    "has",
    "how",
    "into",
    "its",
    "not",
    "one",
    "or",
    "says",
    "the",
    "their",
    "them",
    "then",
    "this",
    "that",
    "use",
    "used",
    "user",
    "uses",
    "when",
    "where",
    "which",
    "with",
    "you",
    "your",
})
KEEP_DECISIONS = frozenset({"keep-mine", "keep-theirs", "keep-both", "merged", "skip"})
ALLOWED_DECISIONS = {
    "install": frozenset({"install", "skip"}),
    "update": frozenset({"update", "skip"}),
    "unchanged": frozenset({"skip"}),
    "modified-locally": KEEP_DECISIONS,
    "collision": KEEP_DECISIONS,
    "migrate-symlink": frozenset({"install", "skip"}),
    "duplicate": frozenset({"remove-duplicate", "skip"}),
}
RESULT_FOR_DECISION = {
    "install": "installed",
    "update": "updated",
    "keep-theirs": "updated",
    "keep-both": "kept-both",
    "keep-mine": "kept",
    "merged": "merged",
    "remove-duplicate": "removed-duplicates",
    "skip": "skipped",
}
RESULT_NAMES = [
    "installed",
    "updated",
    "unchanged",
    "skipped",
    "merged",
    "kept",
    "kept-both",
    "removed-duplicates",
    "backups",
]


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


def has_hook(entries: list, command: str) -> bool:
    return any(
        command == hook.get("command")
        for entry in entries
        for hook in (entry, *entry.get("hooks", []))
    )


def add_claude_hook(installer: Installer, path: Path, command: str) -> None:
    original = installer.read_json(path)
    settings = json.loads(json.dumps(original))
    entries = settings.setdefault("hooks", {}).setdefault("PostToolUse", [])
    if not has_hook(entries, command):
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
    if not has_hook(entries, command):
        entries.append({"command": command, "matcher": CURSOR_HOOK_MATCHER})
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


def user_skills_directory(tool: str) -> Path:
    return Path.home() / f".{tool}" / "skills"


def toolkit_config_path() -> Path:
    return Path.home() / ".config" / "mstack" / "config.json"


def known_overlaps_path() -> Path:
    return SKILLS_SOURCE / SETUP_SKILL / "references" / "known-overlaps.json"


def parse_tools(value: str) -> list[str]:
    tools = sorted({tool.strip() for tool in value.split(",") if tool.strip()})
    if not tools or set(tools) - set(TOOLS):
        raise argparse.ArgumentTypeError(
            f"expected claude, cursor or claude,cursor, got {value!r}"
        )
    return tools


def skills_target(tools: list[str]) -> Path:
    # Cursor also loads ~/.claude/skills, so with both tools that folder alone serves both.
    return user_skills_directory("claude" if "claude" in tools else "cursor")


def other_loaded_directories(tools: list[str]) -> list[Path]:
    if "cursor" not in tools:
        return []
    return [user_skills_directory("cursor" if "claude" in tools else "claude")]


def project_skill_directories() -> list[Path]:
    return [
        REPOSITORY_ROOT / ".claude" / "skills",
        REPOSITORY_ROOT / ".cursor" / "skills",
    ]


def display_path(path: Path) -> str:
    home = str(Path.home())
    text = str(path)
    return "~" + text[len(home) :] if text.startswith(home + os.sep) else text


def read_skill(folder: Path) -> dict[str, bytes]:
    files = {}
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if path.is_file() and not set(relative.parts) & IGNORED_NAMES:
            files[relative.as_posix()] = path.read_bytes()
    return files


def digest(files: dict[str, bytes]) -> str:
    hasher = hashlib.sha256()
    for relative in sorted(files):
        hasher.update(relative.encode("utf-8") + b"\0" + files[relative] + b"\0")
    return hasher.hexdigest()


def folder_hash(path: Path) -> str | None:
    return digest(read_skill(path)) if path.is_dir() else None


def read_frontmatter(text: str) -> dict[str, str] | None:
    match = FRONTMATTER.match(text)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and key and not key[0].isspace():
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def skill_frontmatter(folder: Path) -> dict[str, str]:
    try:
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    return read_frontmatter(text) or {}


def rename_skill(files: dict[str, bytes], name: str) -> dict[str, bytes]:
    text = files["SKILL.md"].decode("utf-8")
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("SKILL.md has no frontmatter")
    header = re.sub(
        r"^name:.*$", f"name: {name}", match.group(1), count=1, flags=re.MULTILINE
    )
    renamed = f"---\n{header}\n---\n{text[match.end() :]}"
    return {**files, "SKILL.md": renamed.encode("utf-8")}


def expected_files(source: Path, installed_as: str) -> dict[str, bytes]:
    files = read_skill(source)
    return files if installed_as == source.name else rename_skill(files, installed_as)


def mstack_skills() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_SOURCE.iterdir()
        if path.name != SETUP_SKILL and (path / "SKILL.md").is_file()
    )


def load_manifest(directory: Path) -> dict[str, Any] | None:
    path = directory / MANIFEST_NAME
    if not path.is_file():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict) or not isinstance(manifest.get("skills"), dict):
        return None
    return manifest


def manifest_status(directory: Path, manifest: dict[str, Any] | None) -> str:
    if manifest is not None:
        return "valid"
    if (directory / MANIFEST_NAME).is_file():
        logger.warning(
            "corrupt manifest, every mstack skill is treated as modified: %s",
            display_path(directory / MANIFEST_NAME),
        )
        return "corrupt"
    return "missing"


def manifest_entries(directory: Path) -> dict[str, dict[str, Any]]:
    manifest = load_manifest(directory)
    return manifest["skills"] if manifest else {}


def is_mstack_link(path: Path, name: str) -> bool:
    if not path.is_symlink():
        return False
    target = Path(os.path.normpath(path.parent / os.readlink(path)))
    if target.resolve() == (SKILLS_SOURCE / name).resolve():
        return True
    return (
        target.name == name
        and target.parent.name == "skills"
        and (target.parent.parent / "scripts" / "setup.py").is_file()
    )


def classify_unmanaged(
    manifest_trusted: bool, installed_hash: str, source_hash: str
) -> str:
    if installed_hash == source_hash:
        return "unchanged"
    return "collision" if manifest_trusted else "modified-locally"


def classify_managed(
    entry: dict[str, Any], installed_hash: str, source_hash: str
) -> str:
    if installed_hash != entry.get("hash"):
        return "modified-locally"
    if installed_hash == source_hash:
        return "unchanged"
    if entry.get("state", "installed") == "installed":
        return "update"
    # A kept or merged version stays until the source changes; then the user decides again.
    return (
        "unchanged" if entry.get("source_hash") == source_hash else "modified-locally"
    )


def classify(
    destination: Path,
    entry: dict[str, Any] | None,
    manifest_trusted: bool,
    source_hash: str,
) -> str:
    if is_mstack_link(destination, destination.name):
        return "migrate-symlink"
    if not destination.exists() and not destination.is_symlink():
        return "install"
    installed_hash = folder_hash(destination)
    if installed_hash is None:
        return "collision"
    if entry is None:
        return classify_unmanaged(manifest_trusted, installed_hash, source_hash)
    return classify_managed(entry, installed_hash, source_hash)


def load_known_overlaps() -> dict[tuple[str, str], str]:
    path = known_overlaps_path()
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        (overlap["skill"], overlap["other"]): overlap["reason"]
        for overlap in data.get("overlaps", [])
    }


def name_tokens(name: str) -> set[str]:
    return {token for token in re.split(r"[-_\s]+", name.lower()) if token}


def description_words(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z][a-z0-9]+", text.lower())
        if len(word) > 2 and word not in STOPWORDS
    }


def jaccard(first: set[str], second: set[str]) -> float:
    union = first | second
    return len(first & second) / len(union) if union else 0.0


def is_mstack_copy(path: Path, hashes: set[str]) -> bool:
    return is_mstack_link(path, path.name) or folder_hash(path) in hashes


def foreign_skills(directories: list[Path], sources: list[Path]) -> list[Path]:
    hashes = {digest(read_skill(source)) for source in sources}
    found = []
    for directory in directories:
        if not directory.is_dir():
            continue
        managed = {
            entry.get("installed_as", name)
            for name, entry in manifest_entries(directory).items()
        }
        for child in sorted(directory.iterdir()):
            if (
                child.name.startswith(".")
                or child.name in managed
                or not (child / "SKILL.md").is_file()
                or is_mstack_copy(child, hashes)
            ):
                continue
            found.append(child)
    return found


def similarity(
    source: Path, candidate: Path, overlaps: dict[tuple[str, str], str]
) -> dict[str, Any] | None:
    source_meta = skill_frontmatter(source)
    candidate_meta = skill_frontmatter(candidate)
    candidate_name = candidate_meta.get("name") or candidate.name
    scores = []
    known = overlaps.get((source.name, candidate.name)) or overlaps.get((
        source.name,
        candidate_name,
    ))
    if known:
        scores.append((1.0, f"known overlap: {known}"))
    name_score = jaccard(name_tokens(source.name), name_tokens(candidate_name))
    if name_score >= NAME_THRESHOLD:
        scores.append((name_score, f"name tokens overlap ({name_score:.2f})"))
    description_score = jaccard(
        description_words(source_meta.get("description", "")),
        description_words(candidate_meta.get("description", "")),
    )
    if description_score >= DESCRIPTION_THRESHOLD:
        scores.append((
            description_score,
            f"description words overlap ({description_score:.2f})",
        ))
    if not scores:
        return None
    return {
        "name": candidate_name,
        "path": str(candidate),
        "score": round(max(score for score, _ in scores), 2),
        "reason": "; ".join(reason for _, reason in scores),
    }


def similar_skills(
    source: Path,
    candidates: list[Path],
    overlaps: dict[tuple[str, str], str],
    excluded: set[Path],
) -> list[dict[str, Any]]:
    found = [
        match
        for candidate in candidates
        if candidate not in excluded
        and (match := similarity(source, candidate, overlaps)) is not None
    ]
    return sorted(found, key=lambda match: (-match["score"], match["path"]))


def duplicate_paths(source: Path, tools: list[str]) -> list[Path]:
    paths = []
    source_hash = digest(read_skill(source))
    for directory in other_loaded_directories(tools):
        entry = manifest_entries(directory).get(source.name)
        managed_name = entry.get("installed_as", source.name) if entry else None
        for name in sorted({source.name, managed_name or source.name}):
            path = directory / name
            if (
                is_mstack_link(path, name)
                or (name == managed_name and path.is_dir())
                or folder_hash(path) == source_hash
            ):
                paths.append(path)
    for directory in project_skill_directories():
        if is_mstack_link(directory / source.name, source.name):
            paths.append(directory / source.name)
    return paths


def plan_item(
    source: Path,
    destination: Path,
    entry: dict[str, Any] | None,
    manifest_trusted: bool,
) -> dict[str, Any]:
    source_hash = digest(expected_files(source, destination.name))
    return {
        "id": source.name,
        "skill": source.name,
        "installed_as": destination.name,
        "action": classify(destination, entry, manifest_trusted, source_hash),
        "path": str(destination),
        "source_hash": source_hash,
        "installed_hash": folder_hash(destination),
        "manifest_hash": entry.get("hash") if entry else None,
        "similar_to": [],
    }


def duplicate_item(source: Path, path: Path) -> dict[str, Any]:
    entry = manifest_entries(path.parent).get(source.name)
    return {
        "id": f"{source.name}@{display_path(path.parent)}",
        "skill": source.name,
        "installed_as": path.name,
        "action": "duplicate",
        "path": str(path),
        "source_hash": digest(read_skill(source)),
        "installed_hash": folder_hash(path),
        "manifest_hash": entry.get("hash") if entry else None,
        "similar_to": [],
    }


def configured_targets() -> set[str]:
    try:
        config = json.loads(toolkit_config_path().read_text(encoding="utf-8"))
        return {str(target) for target in config.get("targets", [])}
    except (OSError, ValueError, AttributeError):
        return set()


def build_plan(tools: list[str]) -> dict[str, Any]:
    target = skills_target(tools)
    manifest = load_manifest(target)
    status = manifest_status(target, manifest)
    # Without a manifest, a same-name folder is foreign only if mstack never installed here.
    trusted = status == "valid" or (
        status == "missing" and str(target) not in configured_targets()
    )
    entries = manifest["skills"] if manifest else {}
    sources = mstack_skills()
    overlaps = load_known_overlaps()
    candidates = foreign_skills([target, *other_loaded_directories(tools)], sources)
    items = []
    for source in sources:
        entry = entries.get(source.name)
        destination = target / (entry or {}).get("installed_as", source.name)
        item = plan_item(source, destination, entry, trusted)
        item["similar_to"] = similar_skills(
            source, candidates, overlaps, {destination, target / source.name}
        )
        items.append(item)
        items.extend(
            duplicate_item(source, path) for path in duplicate_paths(source, tools)
        )
    return {
        "version": MANIFEST_VERSION,
        "tools": tools,
        "target": str(target),
        "toolkit_path": str(REPOSITORY_ROOT),
        "source_commit": source_commit(),
        "manifest": status,
        "items": items,
    }


def source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def format_plan(plan: dict[str, Any]) -> str:
    lines = [f"target: {display_path(Path(plan['target']))}", ""]
    for item in plan["items"]:
        similar = ", ".join(
            f"{match['name']} ({match['score']})" for match in item["similar_to"]
        )
        location = display_path(Path(item["path"]))
        line = f"{item['id']:<40} {item['action']:<17} {location}"
        lines.append(line + (f"  similar: {similar}" if similar else ""))
    return "\n".join(lines) + "\n"


def plan_command(arguments: argparse.Namespace) -> int:
    plan = build_plan(arguments.tools)
    sys.stdout.write(
        json.dumps(plan, indent=2) + "\n" if arguments.json else format_plan(plan)
    )
    return 0


def decision_kind(decision: str) -> str:
    return "merged" if decision.startswith("merged:") else decision


def merged_problems(item: dict[str, Any], decision: str) -> list[str]:
    folder = Path(decision.removeprefix("merged:")).expanduser()
    if not (folder / "SKILL.md").is_file():
        return [f"{item['id']}: merged folder has no SKILL.md: {folder}"]
    name = skill_frontmatter(folder).get("name")
    if name != item["installed_as"]:
        return [
            (
                f"{item['id']}: merged SKILL.md must be named "
                f"{item['installed_as']!r}, not {name!r}"
            )
        ]
    return []


def decision_problems(item: dict[str, Any], decision: str | None) -> list[str]:
    if decision is None:
        if item["action"] == "unchanged":
            return []
        return [f"{item['id']}: no decision for action {item['action']!r}"]
    kind = decision_kind(decision)
    if kind not in ALLOWED_DECISIONS[item["action"]]:
        allowed = ", ".join(sorted(ALLOWED_DECISIONS[item["action"]]))
        return [
            f"{item['id']}: {decision!r} is not valid for {item['action']!r} ({allowed})"
        ]
    if kind == "merged":
        return merged_problems(item, decision)
    if kind == "keep-both":
        renamed = Path(item["path"]).parent / f"{MSTACK_PREFIX}{item['skill']}"
        if item["installed_as"] != item["skill"] or renamed.exists():
            return [f"{item['id']}: keep-both needs a free {renamed.name!r}"]
    return []


def stale_problems(plan: dict[str, Any], current: dict[str, Any]) -> list[str]:
    keys = ("action", "path", "source_hash", "installed_hash")
    planned = {item["id"]: [item.get(key) for key in keys] for item in plan["items"]}
    now = {item["id"]: [item.get(key) for key in keys] for item in current["items"]}
    if planned == now:
        return []
    changed = sorted(
        identifier
        for identifier in set(planned) | set(now)
        if planned.get(identifier) != now.get(identifier)
    )
    return [
        f"the plan is stale, run `skills plan` again (changed: {', '.join(changed)})"
    ]


def validate_decisions(
    plan: dict[str, Any], current: dict[str, Any], decisions: dict[str, str]
) -> list[str]:
    problems = stale_problems(plan, current)
    identifiers = {item["id"] for item in current["items"]}
    problems.extend(
        f"{identifier}: not in the plan"
        for identifier in sorted(set(decisions) - identifiers)
    )
    for item in current["items"]:
        problems.extend(decision_problems(item, decisions.get(item["id"])))
    return problems


class SkillApplier:
    def __init__(self, plan: dict[str, Any], dry_run: bool) -> None:
        self.target = Path(plan["target"])
        self.dry_run = dry_run
        self.timestamp = datetime.datetime.now(datetime.UTC).strftime(
            "%Y%m%d-%H%M%S-%f"
        )
        self.manifest = load_manifest(self.target)
        self.entries: dict[str, dict[str, Any]] = json.loads(
            json.dumps(self.manifest["skills"] if self.manifest else {})
        )
        self.results: dict[str, list[str]] = {name: [] for name in RESULT_NAMES}

    def say(self, verb: str, path: Path) -> None:
        logger.info(
            "%s%s: %s", "would " if self.dry_run else "", verb, display_path(path)
        )

    def backup(self, path: Path) -> None:
        if path.is_symlink():
            self.say("remove link", path)
            if not self.dry_run:
                path.unlink()
            return
        if not path.exists():
            return
        backup = path.parent / BACKUPS_NAME / self.timestamp / path.name
        self.say(f"back up to {display_path(backup)}", path)
        if not self.dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, backup)
        self.results["backups"].append(display_path(backup.parent))

    def copy(self, source: Path, destination: Path, files: dict[str, bytes]) -> None:
        self.backup(destination)
        self.say(f"copy {display_path(source)} to", destination)
        if self.dry_run:
            return
        shutil.copytree(
            source, destination, ignore=shutil.ignore_patterns(*IGNORED_NAMES)
        )
        (destination / "SKILL.md").write_bytes(files["SKILL.md"])

    def record(self, item: dict[str, Any], installed_as: str, **fields: Any) -> None:
        entry = {
            "hash": item["source_hash"],
            "source_hash": item["source_hash"],
            **fields,
        }
        if installed_as != item["skill"]:
            entry["installed_as"] = installed_as
        self.entries[item["skill"]] = entry

    def install(self, item: dict[str, Any], installed_as: str) -> None:
        source = SKILLS_SOURCE / item["skill"]
        files = expected_files(source, installed_as)
        self.copy(source, self.target / installed_as, files)
        self.record(
            item,
            installed_as,
            hash=digest(files),
            files=sorted(files),
            source_hash=digest(files),
        )

    def keep_mine(self, item: dict[str, Any]) -> None:
        path = Path(item["path"])
        files = read_skill(path)
        self.say("keep", path)
        self.record(
            item,
            item["installed_as"],
            hash=digest(files),
            files=sorted(files),
            state="kept",
        )

    def merge(self, item: dict[str, Any], folder: Path) -> None:
        files = read_skill(folder)
        destination = Path(item["path"])
        self.copy(folder, destination, files)
        self.record(
            item,
            destination.name,
            hash=digest(files),
            files=sorted(files),
            state="merged",
        )

    def remove_duplicate(self, item: dict[str, Any]) -> None:
        path = Path(item["path"])
        self.backup(path)
        other = manifest_entries(path.parent)
        if path.parent != self.target and item["skill"] in other:
            del other[item["skill"]]
            self.write_manifest(path.parent, other, load_manifest(path.parent))

    def apply(self, item: dict[str, Any], decision: str | None) -> None:
        kind = decision_kind(decision or "unchanged")
        if kind == "unchanged":
            if item["skill"] not in self.entries:
                files = read_skill(Path(item["path"]))
                self.record(item, item["installed_as"], files=sorted(files))
            self.results["unchanged"].append(item["id"])
            return
        handlers: dict[str, Callable[[], None]] = {
            "install": lambda: self.install(item, item["installed_as"]),
            "update": lambda: self.install(item, item["installed_as"]),
            "keep-theirs": lambda: self.install(item, item["installed_as"]),
            "keep-both": lambda: self.install(item, f"{MSTACK_PREFIX}{item['skill']}"),
            "keep-mine": lambda: self.keep_mine(item),
            "merged": lambda: self.merge(
                item, Path(str(decision).removeprefix("merged:")).expanduser()
            ),
            "remove-duplicate": lambda: self.remove_duplicate(item),
            "skip": lambda: None,
        }
        handlers[kind]()
        self.results[RESULT_FOR_DECISION[kind]].append(item["id"])

    def write_manifest(
        self,
        directory: Path,
        entries: dict[str, dict[str, Any]],
        previous: dict[str, Any] | None,
    ) -> None:
        manifest = {
            "version": MANIFEST_VERSION,
            "toolkit_path": str(REPOSITORY_ROOT),
            "source_commit": source_commit(),
            "installed_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "skills": dict(sorted(entries.items())),
        }
        ignored = {"installed_at"}
        if previous and all(
            previous.get(key) == value
            for key, value in manifest.items()
            if key not in ignored
        ):
            return
        if not entries:
            if previous is not None:
                self.say("remove empty manifest", directory / MANIFEST_NAME)
                if not self.dry_run:
                    (directory / MANIFEST_NAME).unlink()
            return
        self.say("write manifest", directory / MANIFEST_NAME)
        if not self.dry_run:
            directory.mkdir(parents=True, exist_ok=True)
            (directory / MANIFEST_NAME).write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )

    def write_config(self) -> None:
        path = toolkit_config_path()
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            previous = {}
        targets = {
            target
            for target in previous.get("targets", [])
            if (Path(target) / MANIFEST_NAME).is_file()
        } | {str(self.target)}
        config = {"toolkit_path": str(REPOSITORY_ROOT), "targets": sorted(targets)}
        if previous == config:
            return
        self.say("write toolkit config", path)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    def finish(self) -> None:
        self.write_manifest(self.target, self.entries, self.manifest)
        self.write_config()
        self.results["backups"] = sorted(set(self.results["backups"]))


def apply_command(arguments: argparse.Namespace) -> int:
    plan = json.loads(Path(arguments.plan).read_text(encoding="utf-8"))
    decisions = json.loads(Path(arguments.decisions).read_text(encoding="utf-8"))
    current = build_plan(plan["tools"])
    problems = validate_decisions(plan, current, decisions)
    if problems:
        for problem in problems:
            logger.error(problem)
        return 1
    applier = SkillApplier(current, arguments.dry_run)
    for item in current["items"]:
        applier.apply(item, decisions.get(item["id"]))
    applier.finish()
    summary = {"dry_run": arguments.dry_run, **applier.results}
    if arguments.json:
        sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    else:
        for name, values in applier.results.items():
            if values:
                logger.info("%s: %s", name, ", ".join(values))
    return 0


def skill_problems(folder: Path) -> list[str]:
    frontmatter = skill_frontmatter(folder)
    problems = []
    if frontmatter.get("name") != folder.name:
        problems.append(
            f"{folder.name}: frontmatter name is {frontmatter.get('name')!r}"
        )
    if not frontmatter.get("description"):
        problems.append(f"{folder.name}: frontmatter has no description")
    if not (folder.parent / "sync-rules" / "references").is_dir():
        problems.append(f"{folder.name}: ../sync-rules/references/ does not resolve")
    return problems


def config_problems() -> list[str]:
    path = toolkit_config_path()
    try:
        toolkit = Path(json.loads(path.read_text(encoding="utf-8"))["toolkit_path"])
    except (OSError, ValueError, KeyError, TypeError):
        return [f"toolkit config is missing or unreadable: {display_path(path)}"]
    if not (toolkit / "scripts").is_dir():
        return [f"toolkit config points to a folder without scripts/: {toolkit}"]
    return []


def verify_command(arguments: argparse.Namespace) -> int:
    target = skills_target(arguments.tools)
    manifest = load_manifest(target)
    problems = [] if manifest else [f"no valid manifest in {display_path(target)}"]
    installed = []
    for name, entry in sorted((manifest or {"skills": {}})["skills"].items()):
        folder = target / entry.get("installed_as", name)
        installed.append(folder.name)
        problems.extend(skill_problems(folder))
    problems.extend(config_problems())
    result = {"target": str(target), "skills": installed, "problems": problems}
    if arguments.json:
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        for problem in problems:
            logger.error(problem)
        logger.info("verified %d skills in %s", len(installed), display_path(target))
    return 1 if problems else 0


def skills_command(arguments: argparse.Namespace) -> int:
    commands: dict[str, Callable[[argparse.Namespace], int]] = {
        "plan": plan_command,
        "apply": apply_command,
        "verify": verify_command,
    }
    return commands[arguments.skills_command](arguments)


def add_skills_parser(subcommands: Any) -> None:
    skills = subcommands.add_parser(
        "skills",
        help=(
            "Install or update the mstack skills in your user skill folder by copy. "
            "Driven by skills/setup-mstack/SKILL.md."
        ),
    )
    actions = skills.add_subparsers(dest="skills_command", required=True)
    plan = actions.add_parser(
        "plan", help="Compare every mstack skill with the target folder."
    )
    verify = actions.add_parser(
        "verify", help="Check the installed skills and the toolkit config."
    )
    for subparser in (plan, verify):
        subparser.add_argument(
            "--tools",
            type=parse_tools,
            required=True,
            help="claude, cursor or claude,cursor: the tools you use.",
        )
        subparser.add_argument("--json", action="store_true", help="JSON output.")
    apply = actions.add_parser(
        "apply", help="Apply one decision per plan item, with backups."
    )
    apply.add_argument("--plan", required=True, help="Output of `plan --json`.")
    apply.add_argument(
        "--decisions",
        required=True,
        help='JSON object {"<item id>": "<decision>"}.',
    )
    apply.add_argument("--dry-run", action="store_true", help="Write nothing.")
    apply.add_argument("--json", action="store_true", help="JSON summary.")


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
    add_skills_parser(subcommands)
    project.add_argument(
        "--claude-settings", choices=["local", "project"], default=None
    )
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
        arguments.claude_settings = arguments.claude_settings or "local"
    return arguments


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="setup: %(message)s")
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    commands: dict[str, Callable[[argparse.Namespace], int]] = {
        "project": project_command,
        "user": user_command,
        "skills": skills_command,
    }
    return commands[arguments.command](arguments)


if __name__ == "__main__":
    sys.exit(main())
