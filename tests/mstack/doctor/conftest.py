import shutil
from pathlib import Path

import pytest

from mstack.doctor.model import Context
from mstack.doctor.targets import skill_sources
from mstack.render import render_rule
from tests.conftest import REPOSITORY_ROOT
from tests.mstack.conftest import init_git_repository


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """A committed copy of the skills and rules, so tests can change upstream."""
    checkout = tmp_path / "checkout"
    ignore = shutil.ignore_patterns("__pycache__")
    for folder in ("skills", "rules", "agents", "mcp", "settings", "instructions"):
        shutil.copytree(REPOSITORY_ROOT / folder, checkout / folder, ignore=ignore)
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
