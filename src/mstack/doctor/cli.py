import importlib.metadata
import shutil
import subprocess

from mstack.doctor.model import Context, Result, install_fix
from mstack.lint import LintError, find_tool


def run_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            [*command, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return (completed.stdout or completed.stderr).strip()


def path_result(context: Context) -> Result:
    running = importlib.metadata.version("mstack")
    found = shutil.which("mstack")
    if not found:
        return Result(
            group="cli",
            check="mstack",
            status="error",
            detail="'mstack' is not on PATH; the skills run it as 'mstack <command>'",
            fix=install_fix(context),
        )
    reported = run_version([found])
    if reported != f"mstack {running}":
        return Result(
            group="cli",
            check="mstack",
            status="error",
            detail=(
                f"{found} reports {reported or 'no version'}, but this is "
                f"mstack {running}"
            ),
            fix=install_fix(context),
        )
    return Result(
        group="cli", check="mstack", status="ok", detail=f"{found} ({running})"
    )


def ast_grep_result(context: Context) -> Result:
    try:
        path = find_tool("ast-grep")
    except LintError as error:
        return Result(
            group="cli",
            check="ast-grep",
            status="error",
            detail=str(error),
            fix=install_fix(context),
        )
    version = run_version([path])
    if version is None:
        return Result(
            group="cli",
            check="ast-grep",
            status="error",
            detail=f"{path} does not run",
            fix=install_fix(context),
        )
    return Result(
        group="cli", check="ast-grep", status="ok", detail=f"{path} ({version})"
    )


def check_cli(context: Context) -> list[Result]:
    return [path_result(context), ast_grep_result(context)]
