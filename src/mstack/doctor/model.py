from collections.abc import Callable
from pathlib import Path
from typing import Literal

from mstack.config import StrictModel
from mstack.platform import Platform, codex_folder

Status = Literal["ok", "warn", "error"]
REPAIR_FIX = "ask your agent to run the repair skill (/repair in Claude Code)"


class Context(StrictModel):
    """What every check gets: the machine and the checkout under inspection."""

    home: Path
    # Where Cursor's user folder lives: the same home, except on WSL (the Windows
    # profile). See mstack.platform.
    cursor_home: Path | None = None
    platform: Platform = "linux"
    tool: str
    checkout: Path | None
    online: bool = False

    @property
    def cursor(self) -> Path:
        return self.cursor_home or self.home

    @property
    def codex(self) -> Path:
        return codex_folder(self.home)


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
