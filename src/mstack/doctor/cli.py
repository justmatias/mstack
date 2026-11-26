import importlib.metadata
import shutil
import subprocess
import tomllib
from pathlib import Path

from mstack.doctor.model import Context, Result, install_fix

RULEPACK_REPOSITORY = "https://github.com/justmatias/rulepack"
RULEPACK_SETUP_FIX = (
    "rerun the mstack setup (.agents/skills/setup-mstack/SKILL.md), "
    "which installs rulepack at the tag the checkout pins"
)


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


def check_mstack_on_path(context: Context) -> Result:
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


def read_rulepack_pin(checkout: Path | None) -> str | None:
    """The tag `[tool.mstack] rulepack` pins, or None when the checkout has none."""
    if checkout is None:
        return None
    try:
        pyproject = tomllib.loads(
            (checkout / "pyproject.toml").read_text(encoding="utf-8")
        )
        pin = pyproject["tool"]["mstack"]["rulepack"]
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
        return None
    return pin if isinstance(pin, str) else None


def build_rulepack_fix(checkout: Path | None) -> str:
    pin = read_rulepack_pin(checkout)
    if pin is None:
        return RULEPACK_SETUP_FIX
    return f"uv tool install --force git+{RULEPACK_REPOSITORY}@{pin}"


def check_rulepack_on_path(context: Context) -> Result:
    fix = build_rulepack_fix(context.checkout)
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
    return [check_mstack_on_path(context), check_rulepack_on_path(context)]
