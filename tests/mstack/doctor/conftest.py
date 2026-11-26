import shutil
import subprocess
from pathlib import Path

import pytest

from mstack.doctor.model import Context
from mstack.doctor.targets import skill_sources
from mstack.render import main as render_main
from mstack.render import render_rule
from tests.conftest import REPOSITORY_ROOT
from tests.mstack.helpers import git, init_git_repository


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    return home


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """A committed copy of the skills and rules, so tests can change upstream."""
    checkout = tmp_path / "checkout"
    ignore = shutil.ignore_patterns("__pycache__")
    for folder in ("skills", "rules", "agents", "mcp", "settings", "instructions"):
        source = REPOSITORY_ROOT / folder
        destination = checkout / folder
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore)
        else:
            destination.mkdir(parents=True)
    (checkout / "rules" / "error-handling.mdc").write_text(
        "# Error handling\n\n- Explain recovery decisions.\n",
        encoding="utf-8",
    )
    return init_git_repository(checkout)


@pytest.fixture
def installed_home(home: Path, checkout: Path) -> Path:
    """What setup leaves for Claude Code: every skill and rendered rule."""
    for name, skill in skill_sources(checkout).items():
        shutil.copytree(skill, home / ".claude" / "skills" / name)
    rules = home / ".claude" / "rules"
    rules.mkdir(parents=True)
    for mdc in (checkout / "rules").glob("*.mdc"):
        (rules / f"{mdc.stem}.md").write_text(
            render_rule(mdc.read_text(encoding="utf-8")), encoding="utf-8"
        )
    return home


@pytest.fixture
def context(home: Path, checkout: Path):
    def build(**overrides) -> Context:
        values = {"home": home, "tool": "claude", "checkout": checkout} | overrides
        return Context(**values)

    return build


@pytest.fixture
def codex_install(capsys, home, checkout, monkeypatch):
    folder = home / "codex-profile"
    folder.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(folder))
    for name, source in skill_sources(checkout).items():
        shutil.copytree(source, home / ".agents" / "skills" / name)
    (checkout / "instructions" / "global.md").write_text(
        "Global guidance.\n", encoding="utf-8"
    )
    assert render_main(["--combined", str(checkout)]) == 0
    block = capsys.readouterr().out
    (folder / "AGENTS.md").write_text(
        f"Personal guidance.\n\n{block}", encoding="utf-8"
    )
    return folder


@pytest.fixture
def origin_with_tag(checkout: Path, tmp_path: Path):
    def tag(version: str) -> None:
        origin = tmp_path / "origin.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(origin)], check=True)
        git(checkout, "remote", "add", "origin", str(origin))
        git(checkout, "tag", version)
        git(checkout, "push", "--quiet", "origin", "--tags")

    return tag


@pytest.fixture
def write_settings_file(home: Path):
    """Writes agent settings under the home whose one hook runs `command`."""

    def write(relative_path: str, command: str) -> Path:
        path = home / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".toml":
            content = f'[[hooks.Stop]]\nhooks = [{{ command = "{command}" }}]\n'
        else:
            content = (
                f'{{"hooks": {{"Stop": [{{"hooks": [{{"command": "{command}"}}]}}]}}}}'
            )
        path.write_text(content, encoding="utf-8")
        return path

    return write


@pytest.fixture
def _hide_rulepack_from_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mstack.doctor.cli.shutil.which",
        lambda name: None if name == "rulepack" else name,
    )
