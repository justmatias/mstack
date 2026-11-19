import importlib.util
import json
from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT


@pytest.fixture
def sandbox_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    skill = root / "skills" / "sync-rules"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: sync-rules\n---\n")
    return root


@pytest.fixture
def home_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def setup_module(
    sandbox_root: Path,
    # Requested only so HOME points at the sandbox before the module loads.
    home_directory: Path,  # pylint: disable=unused-argument
    monkeypatch: pytest.MonkeyPatch,
):
    specification = importlib.util.spec_from_file_location(
        "setup_cli", REPOSITORY_ROOT / "scripts" / "setup.py"
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module, "REPOSITORY_ROOT", sandbox_root)
    monkeypatch.setattr(module, "SKILLS_SOURCE", sandbox_root / "skills")
    return module


@pytest.fixture
def existing_claude_settings(sandbox_root: Path) -> dict:
    settings = {
        "permissions": {"allow": ["Bash(make:*)"]},
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo done"}],
                }
            ]
        },
    }
    path = sandbox_root / ".claude" / "settings.local.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(settings))
    return settings


@pytest.fixture
def agent_components() -> list[str]:
    return ["--with", "claude-hook", "--with", "cursor-hook"]
