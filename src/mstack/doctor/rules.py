from mstack.doctor.model import REPAIR_FIX, Context, Result
from mstack.doctor.targets import rule_names, uses_claude


def check_rules(context: Context) -> list[Result]:
    """Claude Code user rules; Cursor keeps its user rules in its settings instead."""
    if not uses_claude(context.tool) or context.checkout is None:
        return []
    folder = context.home / ".claude" / "rules"
    names = rule_names(context.checkout)
    missing = [name for name in names if not (folder / f"{name}.md").is_file()]
    with_frontmatter = [
        name
        for name in names
        if name not in missing
        and (folder / f"{name}.md").read_text(encoding="utf-8").startswith("---")
    ]
    results = []
    if missing:
        results.append(
            Result(
                group="rules",
                check="installed",
                status="error",
                detail=f"not installed in {folder}: {', '.join(missing)}",
                fix=REPAIR_FIX,
            )
        )
    if with_frontmatter:
        results.append(
            Result(
                group="rules",
                check="frontmatter",
                status="error",
                detail=(
                    "installed with frontmatter (Claude Code may not load them): "
                    + ", ".join(with_frontmatter)
                ),
                fix=REPAIR_FIX,
            )
        )
    if not results:
        results.append(
            Result(
                group="rules",
                check="installed",
                status="ok",
                detail=f"{len(names)} mstack rules in {folder}",
            )
        )
    return results
