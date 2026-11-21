from pathlib import Path

from mstack.doctor.model import REPAIR_FIX, Context, Result
from mstack.doctor.targets import (
    codex_instructions,
    rule_names,
    uses_claude,
    uses_codex,
)
from mstack.render import BLOCK_END, BLOCK_START


def codex_block(path: Path) -> str | None:
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [index for index, line in enumerate(lines) if line == BLOCK_START]
    ends = [index for index, line in enumerate(lines) if line == BLOCK_END]
    if len(starts) == len(ends) == 1 and starts[0] < ends[0]:
        return "\n".join(lines[starts[0] : ends[0] + 1]) + "\n"
    return None


def check_codex_rules(context: Context) -> Result:
    path = codex_instructions(context.codex)
    if codex_block(path) is None:
        return Result(
            group="rules",
            check="codex",
            status="error",
            detail=f"expected one mstack managed block in {path}",
            fix=REPAIR_FIX,
        )
    return Result(
        group="rules", check="codex", status="ok", detail=f"mstack rules in {path}"
    )


def check_rules(context: Context) -> list[Result]:
    if context.checkout is None:
        return []
    results = [check_codex_rules(context)] if uses_codex(context.tool) else []
    if uses_claude(context.tool):
        results.extend(check_claude_rules(context))
    return results


def check_claude_rules(context: Context) -> list[Result]:
    assert context.checkout is not None
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
