from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mstack.install.item_kinds import Tool
from mstack.platform import Platform

Status = Literal["ok", "warn", "error"]
SETUP_FIX = "ask your agent to follow skills/setup-mstack/SKILL.md in the checkout"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Context(StrictModel):
    """What every check gets: the machine and the checkout under inspection."""

    home: Path
    # Where Cursor's user folder lives: the same home, except on WSL (the Windows
    # profile). See mstack.platform.
    cursor_home: Path | None = None
    platform: Platform = "linux"
    tool: Tool
    checkout: Path | None
    online: bool = False

    @property
    def cursor(self) -> Path:
        return self.cursor_home or self.home


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
