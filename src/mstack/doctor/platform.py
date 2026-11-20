from mstack.doctor.model import Context, Result
from mstack.install.item_kinds import uses_cursor
from mstack.platform import WINDOWS_HOME_VARIABLE


def check_platform(context: Context) -> list[Result]:
    """On WSL, Cursor on Windows reads the Windows profile, not ~/.cursor."""
    if context.platform != "wsl" or not uses_cursor(context.tool):
        return []
    if context.cursor == context.home:
        return [
            Result(
                group="platform",
                check="wsl-cursor",
                status="warn",
                detail=(
                    "this is WSL, and the Windows profile was not found: Cursor on "
                    f"Windows does not read {context.home / '.cursor'}"
                ),
                fix=f"set {WINDOWS_HOME_VARIABLE} to /mnt/c/Users/<user>",
            )
        ]
    return [
        Result(
            group="platform",
            check="wsl-cursor",
            status="ok",
            detail=f"WSL: Cursor's files are in {context.cursor / '.cursor'}",
        )
    ]
