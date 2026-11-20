import argparse
import json
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote

from mstack.guards.credit import credit_problems
from mstack.render import FRONTMATTER_DELIMITER, FrontmatterError, split_frontmatter

logger = logging.getLogger(__name__)

SKILL_FILE = "SKILL.md"
PROFILES = ("mstack", "generic")
MAX_DESCRIPTION_LENGTH = 1024
KEBAB_CASE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"(`+).+?\1")
QUOTED = re.compile(r"\"[^\"]*\"|“[^”]*”")
LINK = re.compile(r"\[[^\]]*\]\(\s*<?(?P<target>[^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
EXTERNAL_LINK = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|#|/|~)")
PRINCIPLES_HEADER = "> **Principles (always apply):**"
AUXILIARY_FOLDERS = ("references", "scripts")
# Keys mstack's own skills use. Any other key is an error under the mstack profile.
MSTACK_KEYS = {"name", "description", "license", "metadata", "disable-model-invocation"}
# Optional keys that Claude Code or Cursor accept. Under the generic profile, any
# other key is only a warning.
GENERIC_KEYS = MSTACK_KEYS | {
    "agent",
    "allowed-tools",
    "argument-hint",
    "compatibility",
    "context",
    "effort",
    "hooks",
    "model",
    "paths",
    "user-invocable",
    "version",
    "when_to_use",
}


def issue(
    skill: Path, check: str, detail: str, *, file: Path | None = None, line: int = 1
) -> dict:
    path = file or skill / SKILL_FILE
    return {
        "skill": skill.name,
        "check": check,
        "severity": "error",
        "file": f"{path}:{line}",
        "detail": detail,
    }


def warning(
    skill: Path, check: str, detail: str, *, file: Path | None = None, line: int = 1
) -> dict:
    return issue(skill, check, detail, file=file, line=line) | {"severity": "warning"}


def find_skills(directories: list[Path]) -> tuple[list[Path], list[Path]]:
    skills: list[Path] = []
    missing: list[Path] = []
    for directory in directories:
        if not directory.is_dir():
            missing.append(directory)
        elif (directory / SKILL_FILE).is_file():
            skills.append(directory)
        else:
            skills.extend(
                child
                for child in sorted(directory.iterdir())
                if not child.name.startswith(".") and (child / SKILL_FILE).is_file()
            )
    return skills, missing


def prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield each line outside fenced code blocks, with its code spans removed."""
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line_number, CODE_SPAN.sub("", line)


def markdown_files(skill: Path) -> list[Path]:
    return sorted(path for path in skill.rglob("*.md") if path.is_file())


def load_frontmatter(skill: Path, text: str) -> tuple[dict | None, list[dict]]:
    if text.split("\n", 1)[0].strip() != FRONTMATTER_DELIMITER:
        return None, [issue(skill, "frontmatter", "no '---' frontmatter block")]
    try:
        frontmatter, _ = split_frontmatter(text)
    except FrontmatterError as error:
        return None, [issue(skill, "frontmatter", str(error))]
    return frontmatter, []


def name_issues(skill: Path, frontmatter: dict) -> list[dict]:
    name = frontmatter.get("name")
    if not isinstance(name, str) or not name:
        return [issue(skill, "name", "missing 'name'")]
    if not KEBAB_CASE.match(name):
        return [issue(skill, "name", f"'{name}' is not kebab-case")]
    if name != skill.name:
        return [issue(skill, "name", f"'{name}' does not match the folder name")]
    return []


def description_issues(skill: Path, frontmatter: dict) -> list[dict]:
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        return [issue(skill, "description", "missing or empty 'description'")]
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return [
            issue(
                skill,
                "description",
                f"is {len(description)} characters, over {MAX_DESCRIPTION_LENGTH}",
            )
        ]
    return []


def key_issues(skill: Path, frontmatter: dict, profile: str) -> list[dict]:
    known = MSTACK_KEYS if profile == "mstack" else GENERIC_KEYS
    report = issue if profile == "mstack" else warning
    return [
        report(skill, "keys", f"unknown frontmatter key '{key}'")
        for key in frontmatter
        if key not in known
    ]


def credit_issues(skill: Path, frontmatter: dict) -> list[dict]:
    return [issue(skill, "credit", problem) for problem in credit_problems(frontmatter)]


def principles_issues(skill: Path, text: str) -> list[dict]:
    try:
        _, body = split_frontmatter(text)
    except FrontmatterError:
        body = text
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    title = next(
        (index for index, line in enumerate(lines) if line.startswith("# ")), None
    )
    if title is None:
        return [issue(skill, "principles", "no '# ' title")]
    following = lines[title + 1] if title + 1 < len(lines) else ""
    if not following.startswith(PRINCIPLES_HEADER):
        return [
            issue(
                skill,
                "principles",
                f"the first block after the title is not the '{PRINCIPLES_HEADER}' "
                "header",
            )
        ]
    return []


def link_targets(path: Path) -> Iterator[tuple[int, str, Path]]:
    for line_number, line in prose_lines(path.read_text(encoding="utf-8")):
        for match in LINK.finditer(line):
            target = match["target"]
            if EXTERNAL_LINK.match(target):
                continue
            relative = unquote(target.split("#", 1)[0])
            if relative:
                yield line_number, target, (path.parent / relative).resolve()


def link_issues(skill: Path, root: Path) -> tuple[list[dict], set[Path]]:
    problems: list[dict] = []
    linked: set[Path] = set()
    for path in markdown_files(skill):
        for line_number, target, resolved in link_targets(path):
            linked.add(resolved)
            if not resolved.is_relative_to(root.resolve()):
                detail = f"'{target}' points outside the skills folder"
            elif not resolved.exists():
                detail = f"'{target}' does not exist"
            else:
                continue
            problems.append(issue(skill, "links", detail, file=path, line=line_number))
    return problems, linked


def is_mentioned(skill: Path, file: Path, texts: dict[Path, str]) -> bool:
    relative = file.relative_to(skill).as_posix()
    qualified = f"{skill.name}/{relative}"
    return any(
        qualified in text or (source.is_relative_to(skill) and relative in text)
        for source, text in texts.items()
        if source != file
    )


def unused_file_issues(
    skill: Path, linked: set[Path], texts: dict[Path, str]
) -> list[dict]:
    files = [
        path
        for folder in AUXILIARY_FOLDERS
        for path in sorted((skill / folder).rglob("*"))
        if path.is_file()
    ]
    return [
        warning(skill, "unused-files", "is linked from nowhere", file=path)
        for path in files
        if path.resolve() not in linked and not is_mentioned(skill, path, texts)
    ]


def english_issues(skill: Path) -> list[dict]:
    problems: list[dict] = []
    for path in markdown_files(skill):
        for line_number, line in prose_lines(path.read_text(encoding="utf-8")):
            letters = sorted({
                character
                for character in QUOTED.sub("", line)
                if not character.isascii() and character.isalpha()
            })
            if letters:
                problems.append(
                    warning(
                        skill,
                        "english",
                        f"non-ASCII letters {' '.join(letters)}",
                        file=path,
                        line=line_number,
                    )
                )
    return problems


def frontmatter_issues(skill: Path, text: str, profile: str) -> list[dict]:
    frontmatter, problems = load_frontmatter(skill, text)
    if frontmatter is None:
        return problems
    problems = name_issues(skill, frontmatter) + description_issues(skill, frontmatter)
    problems.extend(key_issues(skill, frontmatter, profile))
    if profile == "mstack":
        problems.extend(credit_issues(skill, frontmatter))
    return problems


def skill_issues(
    skill: Path, profile: str, linked: set[Path], texts: dict[Path, str]
) -> list[dict]:
    text = (skill / SKILL_FILE).read_text(encoding="utf-8")
    problems = frontmatter_issues(skill, text, profile)
    problems.extend(unused_file_issues(skill, linked, texts))
    if profile == "mstack":
        problems.extend(principles_issues(skill, text))
        problems.extend(english_issues(skill))
    return problems


def check_skills(directories: list[Path], profile: str = "mstack") -> dict:
    """Validate every skill under the given folders. `doctor` reuses this."""
    skills, missing = find_skills(directories)
    issues: list[dict] = [
        {
            "skill": None,
            "check": "folder",
            "severity": "error",
            "file": str(directory),
            "detail": "is not a folder",
        }
        for directory in missing
    ]
    linked: set[Path] = set()
    texts: dict[Path, str] = {}
    for skill in skills:
        skill_links, skill_linked = link_issues(skill, skill.parent)
        issues.extend(skill_links)
        linked |= skill_linked
        texts.update(
            (path, path.read_text(encoding="utf-8")) for path in markdown_files(skill)
        )
    for skill in skills:
        issues.extend(skill_issues(skill, profile, linked, texts))
    return {
        "ok": not any(entry["severity"] == "error" for entry in issues),
        "profile": profile,
        "skills": [skill.name for skill in skills],
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack skills-check",
        description=(
            "Validate every skill (a folder with a SKILL.md): frontmatter, name, "
            "description, links and, for mstack's own skills, their conventions."
        ),
    )
    parser.add_argument(
        "directories",
        nargs="*",
        type=Path,
        default=[Path("skills")],
        help="Folders of skills, or skill folders (default: skills/).",
    )
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="mstack",
        help="'generic' skips the mstack-only checks, for skills that aren't mstack's.",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    arguments = parser.parse_args(argv)

    report = check_skills(
        [directory.expanduser() for directory in arguments.directories],
        arguments.profile,
    )
    if arguments.json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        for entry in report["issues"]:
            log = logger.error if entry["severity"] == "error" else logger.warning
            log("%s: [%s] %s", entry["file"], entry["check"], entry["detail"])
        if report["ok"]:
            logger.info("check_skills: OK (%d skills)", len(report["skills"]))
    return 0 if report["ok"] else 1
