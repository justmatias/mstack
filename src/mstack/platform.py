"""Where each tool keeps its user-level files, on Linux, macOS, Windows and WSL.

Every tool uses the user's home, except Cursor on WSL: Cursor runs on Windows and
reads the Windows profile (`.cursor` under `%USERPROFILE%`), not `~/.cursor` inside WSL.
So on WSL the two tools live in different homes, and "both" means two copies.
"""

import argparse
import functools
import json
import logging
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

Platform = Literal["linux", "macos", "windows", "wsl"]
PLATFORMS: tuple[Platform, ...] = ("linux", "macos", "windows", "wsl")
PROC_VERSION = Path("/proc/version")
# Overrides for machines where detection fails (and for tests).
PLATFORM_VARIABLE = "MSTACK_PLATFORM"
WINDOWS_HOME_VARIABLE = "MSTACK_WINDOWS_HOME"


def detect(
    system: str | None = None,
    proc_version: Path = PROC_VERSION,
    environ: Mapping[str, str] | None = None,
) -> Platform:
    environ = os.environ if environ is None else environ
    override = environ.get(PLATFORM_VARIABLE)
    if override in PLATFORMS:
        return override
    system = system or sys.platform
    if system == "win32":
        return "windows"
    if system == "darwin":
        return "macos"
    try:
        if "microsoft" in proc_version.read_text(encoding="utf-8").lower():
            return "wsl"
    except OSError:
        pass
    return "linux"


def run_quiet(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = completed.stdout.strip()
    return output if completed.returncode == 0 and output else None


def wsl_windows_home(environ: Mapping[str, str] | None = None) -> Path | None:
    """The Windows profile as a WSL path: MSTACK_WINDOWS_HOME, else from cmd.exe."""
    environ = os.environ if environ is None else environ
    if override := environ.get(WINDOWS_HOME_VARIABLE):
        return Path(override).expanduser()
    return windows_profile_from_cmd()


@functools.cache
def windows_profile_from_cmd() -> Path | None:
    """Asks Windows once per process: starting cmd.exe from WSL is slow."""
    profile = run_quiet(["cmd.exe", "/c", "echo %USERPROFILE%"])
    if profile is None or "%" in profile:
        return None
    converted = run_quiet(["wslpath", "-u", profile])
    return Path(converted) if converted else None


def tool_homes(
    platform: Platform | None = None, environ: Mapping[str, str] | None = None
) -> dict[str, Path]:
    """The home each tool's user folder lives in (`<home>/.claude`, `<home>/.cursor`)."""
    platform = platform or detect(environ=environ)
    home = Path.home()
    cursor_home = home
    if platform == "wsl":
        windows_home = wsl_windows_home(environ)
        if windows_home is None:
            logger.warning(
                "platform: WSL, but the Windows profile was not found; Cursor on "
                "Windows will not see ~/.cursor. Set %s to it (/mnt/c/Users/<user>).",
                WINDOWS_HOME_VARIABLE,
            )
        else:
            cursor_home = windows_home
    return {"claude": home, "cursor": cursor_home}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mstack platform",
        description=(
            "Print the detected platform and the home each tool's user folder is "
            f"in. {PLATFORM_VARIABLE} and {WINDOWS_HOME_VARIABLE} override detection."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    arguments = parser.parse_args(argv)
    platform = detect()
    homes = tool_homes(platform)
    if arguments.json:
        payload = {
            "platform": platform,
            "homes": {tool: str(home) for tool, home in homes.items()},
            "folders": {tool: str(home / f".{tool}") for tool, home in homes.items()},
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0
    lines = [f"platform: {platform}"]
    lines.extend(f"{tool}: {home / f'.{tool}'}" for tool, home in homes.items())
    sys.stdout.write("\n".join(lines) + "\n")
    return 0
