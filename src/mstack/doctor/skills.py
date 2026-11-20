from pathlib import Path

from mstack.doctor.model import SETUP_FIX, Context, Result
from mstack.guards.check_skills import check_skills
from mstack.install.item_kinds import source_names, uses_claude, uses_cursor


def skills_folders(context: Context) -> list[Path]:
    """With both tools, skills go to ~/.claude only, because Cursor loads that folder
    too, unless Cursor lives in another home (WSL): then each tool gets a copy."""
    claude = context.home / ".claude" / "skills"
    cursor = context.cursor / ".cursor" / "skills"
    if not uses_cursor(context.tool):
        return [claude]
    if not uses_claude(context.tool):
        return [cursor]
    return [claude, cursor] if context.cursor != context.home else [claude]


def missing_results(context: Context, folder: Path) -> list[Result]:
    if context.checkout is None:
        return []
    names = source_names(context.checkout, "skill")
    missing = [name for name in names if not (folder / name / "SKILL.md").is_file()]
    if missing:
        return [
            Result(
                group="skills",
                check="installed",
                status="error",
                detail=f"not installed in {folder}: {', '.join(missing)}",
                fix=SETUP_FIX,
            )
        ]
    return [
        Result(
            group="skills",
            check="installed",
            status="ok",
            detail=f"{len(names)} mstack skills in {folder}",
        )
    ]


def validation_results(folder: Path) -> list[Result]:
    if not folder.is_dir():
        return []
    report = check_skills([folder], profile="generic")
    errors = [issue for issue in report["issues"] if issue["severity"] == "error"]
    if not errors:
        return [
            Result(
                group="skills",
                check="valid",
                status="ok",
                detail=f"{len(report['skills'])} skills pass skills-check --profile generic",
            )
        ]
    return [
        Result(
            group="skills",
            check="valid",
            status="error",
            detail=f"{issue['file']}: [{issue['check']}] {issue['detail']}",
            fix=f"mstack skills-check {folder} --profile generic",
        )
        for issue in errors
    ]


def duplicate_results(context: Context) -> list[Result]:
    """Only when Cursor shares the home: it then loads ~/.claude/skills as well."""
    claude = context.home / ".claude" / "skills"
    cursor = context.cursor / ".cursor" / "skills"
    if context.cursor != context.home or not (claude.is_dir() and cursor.is_dir()):
        return []
    names = {path.name for path in claude.iterdir() if (path / "SKILL.md").is_file()}
    duplicates = sorted(
        path.name
        for path in cursor.iterdir()
        if path.name in names and (path / "SKILL.md").is_file()
    )
    if not duplicates:
        return []
    return [
        Result(
            group="skills",
            check="duplicates",
            status="warn",
            detail=(
                f"in both {claude} and {cursor} (Cursor shows them twice): "
                + ", ".join(duplicates)
            ),
            fix=f"delete the copies in {cursor}",
        )
    ]


def check_skills_installed(context: Context) -> list[Result]:
    results = []
    for folder in skills_folders(context):
        results += missing_results(context, folder) + validation_results(folder)
    return results + duplicate_results(context)
