"""Installed copies that no longer match the checkout.

Doctor does not know why a copy differs: the user may have edited it, or the
checkout may have moved on. The repair skill reads the diff and the checkout's
history to tell which, and asks before touching the user's edits.
"""

from pathlib import Path

from mstack.doctor.model import REPAIR_FIX, Context, Result
from mstack.doctor.targets import (
    agent_names,
    copied_folders,
    file_content,
    rule_names,
    same_tree,
    skill_sources,
    uses_claude,
)
from mstack.render import FrontmatterError, render_rule


def drifted(kind: str, name: str, installed: Path) -> Result:
    return Result(
        group="drift",
        check=f"{kind} {name}",
        status="warn",
        detail=f"{installed} differs from the checkout",
        fix=REPAIR_FIX,
    )


def skill_drift(context: Context, checkout: Path) -> list[Result]:
    results = []
    for folder in copied_folders(context.tool, context.home, context.cursor, "skills"):
        for name, source in skill_sources(checkout).items():
            installed = folder / name
            if (installed / "SKILL.md").is_file() and not same_tree(source, installed):
                results.append(drifted("skill", name, installed))
    return results


def agent_drift(context: Context, checkout: Path) -> list[Result]:
    results = []
    for folder in copied_folders(context.tool, context.home, context.cursor, "agents"):
        for name in agent_names(checkout):
            installed = folder / f"{name}.md"
            source = checkout / "agents" / f"{name}.md"
            if installed.is_file() and file_content(installed) != file_content(source):
                results.append(drifted("agent", name, installed))
    return results


def rule_drift(context: Context, checkout: Path) -> list[Result]:
    if not uses_claude(context.tool):
        return []
    results = []
    folder = context.home / ".claude" / "rules"
    for name in rule_names(checkout):
        installed = folder / f"{name}.md"
        if not installed.is_file():
            continue
        try:
            expected = render_rule(
                (checkout / "rules" / f"{name}.mdc").read_text(encoding="utf-8")
            )
        except FrontmatterError as error:
            results.append(
                Result(
                    group="drift",
                    check=f"rule {name}",
                    status="error",
                    detail=f"the checkout's rule cannot be rendered: {error}",
                )
            )
            continue
        if file_content(installed).decode("utf-8") != expected:
            results.append(drifted("rule", name, installed))
    return results


def check_drift(context: Context) -> list[Result]:
    checkout = context.checkout
    if checkout is None or not checkout.is_dir():
        return []
    results = (
        skill_drift(context, checkout)
        + rule_drift(context, checkout)
        + agent_drift(context, checkout)
    )
    if results:
        return results
    return [
        Result(
            group="drift",
            check="checkout",
            status="ok",
            detail="every installed skill, rule and agent matches the checkout",
        )
    ]
