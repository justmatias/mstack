from itertools import combinations
from pathlib import Path

from mstack.doctor.model import REPAIR_FIX, Context, Result
from mstack.doctor.targets import skill_folders, skill_names, uses_cursor
from mstack.guards.check_skills import check_skills


def missing_results(context: Context, folder: Path) -> list[Result]:
    if context.checkout is None:
        return []
    names = skill_names(context.checkout)
    missing = [name for name in names if not (folder / name / "SKILL.md").is_file()]
    if missing:
        return [
            Result(
                group="skills",
                check="installed",
                status="error",
                detail=f"not installed in {folder}: {', '.join(missing)}",
                fix=REPAIR_FIX,
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
    if not uses_cursor(context.tool):
        return []
    # Cursor reads these compatibility folders from its own home, including on WSL.
    # https://cursor.com/docs/skills
    folders = {
        folder: {path.parent.name for path in folder.glob("*/SKILL.md")}
        for folder in (
            context.cursor / name / "skills"
            for name in (".claude", ".cursor", ".agents", ".codex")
        )
    }
    return [
        Result(
            group="skills",
            check="duplicates",
            status="warn",
            detail=(
                f"in both {first} and {second} (Cursor shows them twice): "
                + ", ".join(sorted(duplicates))
            ),
            fix="review the copies and back up redundant ones before removing them",
        )
        for first, second in combinations(folders, 2)
        if (duplicates := folders[first] & folders[second])
    ]


def check_skills_installed(context: Context) -> list[Result]:
    results = []
    for folder in skill_folders(context.tool, context.home, context.cursor):
        results += missing_results(context, folder) + validation_results(folder)
    return results + duplicate_results(context)
