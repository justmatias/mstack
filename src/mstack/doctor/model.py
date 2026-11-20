from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mstack.install.item_kinds import Tool

Status = Literal["ok", "warn", "error"]
SETUP_FIX = "ask your agent to follow skills/setup-mstack/SKILL.md in the checkout"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Context(StrictModel):
    """What every check gets: the machine and the checkout under inspection."""

    home: Path
    tool: Tool
    checkout: Path | None
    online: bool = False


class Result(StrictModel):
    group: str
    check: str
    status: Status
    detail: str
    fix: str | None = None


Check = Callable[[Context], list[Result]]


def install_fix(context: Context) -> str:
    checkout = context.checkout or "<mstack checkout>"
    return f"uv tool install --editable {checkout}"
