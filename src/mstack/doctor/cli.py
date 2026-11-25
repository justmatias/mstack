import importlib.metadata
import shutil
import subprocess
import tomllib

from mstack.doctor.model import Context, Result, install_fix

RULEPACK_REPOSITORY = "https://github.com/justmatias/rulepack"


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


def rulepack_pin(context: Context) -> str:
    """The rulepack tag that `[tool.mstack] rulepack` in the checkout pins."""
    pyproject = context.checkout / "pyproject.toml" if context.checkout else None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8")) if pyproject else {}
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    tool = data.get("tool")
    settings = tool.get("mstack") if isinstance(tool, dict) else None
    pin = settings.get("rulepack") if isinstance(settings, dict) else None
    return pin if isinstance(pin, str) else "<tag>"


def rulepack_result(context: Context) -> Result:
    fix = f"uv tool install git+{RULEPACK_REPOSITORY}@{rulepack_pin(context)}"
    found = shutil.which("rulepack")
    if not found:
        return Result(
            group="cli",
            check="rulepack",
            status="error",
            detail="'rulepack' is not on PATH; the agent hooks and the skills run it",
            fix=fix,
        )
    version = run_version([found])
    if version is None:
        return Result(
            group="cli",
            check="rulepack",
            status="error",
            detail=f"{found} does not run",
            fix=fix,
        )
    return Result(
        group="cli", check="rulepack", status="ok", detail=f"{found} ({version})"
    )


def check_cli(context: Context) -> list[Result]:
    return [path_result(context), rulepack_result(context)]
