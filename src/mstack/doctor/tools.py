import shutil

from mstack.doctor.model import Context, Result, StrictModel


class ExternalTool(StrictModel):
    required: bool
    used_by: str
    link: str


TOOLS = {
    "uv": ExternalTool(
        required=True,
        used_by="mstack and the checks",
        link="https://docs.astral.sh/uv/",
    ),
    "git": ExternalTool(
        required=True,
        used_by="mstack and the checks",
        link="https://git-scm.com/downloads",
    ),
    "gh": ExternalTool(
        required=False,
        used_by="correct and integrate",
        link="https://cli.github.com/",
    ),
}


def check_tools(_context: Context) -> list[Result]:
    results = []
    for name, tool in TOOLS.items():
        found = shutil.which(name)
        if found:
            results.append(Result(group="tools", check=name, status="ok", detail=found))
            continue
        results.append(
            Result(
                group="tools",
                check=name,
                status="error" if tool.required else "warn",
                detail=f"'{name}' is not on PATH ({tool.used_by} need it)",
                fix=f"install it: {tool.link}",
            )
        )
    return results
