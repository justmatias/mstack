from pathlib import Path

from mstack.doctor.model import Context, Result
from mstack.install.item_kinds import uses_cursor

PROC_VERSION = Path("/proc/version")
WINDOWS_USERS = Path("/mnt/c/Users")


def is_wsl() -> bool:
    try:
        return "microsoft" in PROC_VERSION.read_text(encoding="utf-8").lower()
    except OSError:
        return False


def check_platform(context: Context) -> list[Result]:
    """On WSL, Cursor running on Windows reads the Windows profile, not ~/.cursor."""
    if not (uses_cursor(context.tool) and is_wsl()):
        return []
    windows_folders = sorted(WINDOWS_USERS.glob("*/.cursor"))
    if not windows_folders:
        return []
    return [
        Result(
            group="platform",
            check="wsl-cursor",
            status="warn",
            detail=(
                "this is WSL: Cursor on Windows reads its skills from "
                + ", ".join(str(folder / "skills") for folder in windows_folders)
                + f", not {context.home / '.cursor' / 'skills'}"
            ),
            fix="install the Cursor skills into the Windows folder",
        )
    ]
