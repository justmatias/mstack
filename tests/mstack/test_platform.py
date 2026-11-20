import logging
from pathlib import Path

import pytest

from mstack import platform
from mstack.platform import detect, tool_homes, wsl_windows_home

NO_OVERRIDE: dict[str, str] = {}


@pytest.fixture
def proc_version(tmp_path: Path):
    def write(text: str) -> Path:
        path = tmp_path / "version"
        path.write_text(text, encoding="utf-8")
        return path

    return write


@pytest.fixture
def windows_commands(monkeypatch: pytest.MonkeyPatch):
    """Fake cmd.exe and wslpath: map each command name to its output (None fails)."""

    def install(outputs: dict[str, str | None]) -> None:
        platform.windows_profile_from_cmd.cache_clear()
        monkeypatch.setattr(
            platform, "run_quiet", lambda command: outputs.get(command[0])
        )

    yield install
    platform.windows_profile_from_cmd.cache_clear()


@pytest.mark.parametrize(
    ("system", "expected"), [("win32", "windows"), ("darwin", "macos")]
)
def test_detects_windows_and_macos(system: str, expected: str, proc_version):
    assert detect(system, proc_version("Linux microsoft"), NO_OVERRIDE) == expected


def test_detects_wsl_from_proc_version(proc_version):
    version = proc_version("Linux version 5.15.167.4-microsoft-standard-WSL2")

    assert detect("linux", version, NO_OVERRIDE) == "wsl"


def test_detects_linux(proc_version):
    assert (
        detect("linux", proc_version("Linux version 6.8.0-generic"), NO_OVERRIDE)
        == "linux"
    )


def test_missing_proc_version_is_linux(tmp_path: Path):
    assert detect("linux", tmp_path / "missing", NO_OVERRIDE) == "linux"


def test_environment_variable_overrides_detection(proc_version):
    environ = {"MSTACK_PLATFORM": "wsl"}

    assert detect("linux", proc_version("Linux"), environ) == "wsl"


def test_windows_home_from_the_environment_variable(windows_commands):
    windows_commands({"cmd.exe": "C:\\Users\\other", "wslpath": "/mnt/c/Users/other"})

    assert wsl_windows_home({"MSTACK_WINDOWS_HOME": "/mnt/d/me"}) == Path("/mnt/d/me")


def test_windows_home_from_cmd_and_wslpath(windows_commands):
    windows_commands({"cmd.exe": "C:\\Users\\me", "wslpath": "/mnt/c/Users/me"})

    assert wsl_windows_home(NO_OVERRIDE) == Path("/mnt/c/Users/me")


@pytest.mark.parametrize(
    "outputs",
    [
        {"cmd.exe": None, "wslpath": "/mnt/c/Users/me"},
        {"cmd.exe": "%USERPROFILE%", "wslpath": "/mnt/c/Users/me"},
        {"cmd.exe": "C:\\Users\\me", "wslpath": None},
    ],
    ids=["no-cmd", "unexpanded", "no-wslpath"],
)
def test_windows_home_is_none_when_windows_does_not_answer(windows_commands, outputs):
    windows_commands(outputs)

    assert wsl_windows_home(NO_OVERRIDE) is None


@pytest.mark.parametrize("name", ["linux", "macos", "windows"])
def test_every_tool_uses_the_home_outside_wsl(name):
    homes = tool_homes(name, NO_OVERRIDE)

    assert homes == {"claude": Path.home(), "cursor": Path.home()}


def test_cursor_uses_the_windows_profile_on_wsl():
    homes = tool_homes("wsl", {"MSTACK_WINDOWS_HOME": "/mnt/c/Users/me"})

    assert homes == {"claude": Path.home(), "cursor": Path("/mnt/c/Users/me")}


def test_wsl_without_windows_profile_falls_back_and_warns(windows_commands, caplog):
    windows_commands({})

    with caplog.at_level(logging.WARNING):
        homes = tool_homes("wsl", NO_OVERRIDE)

    assert homes["cursor"] == Path.home()
    assert "MSTACK_WINDOWS_HOME" in caplog.text
