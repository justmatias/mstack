import importlib.util
import json
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import REPOSITORY_ROOT

SKILL_NAMES = ["correct-rules", "reflect-rules", "sync-rules"]
KNOWN_OVERLAPS = REPOSITORY_ROOT / ".claude" / "skills" / "setup-mstack" / "references"


def write_skill(folder: Path, name: str, description: str) -> None:
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        f'---\nname: {name}\ndescription: "{description}"\n---\n\n# {name}\n'
    )


def snapshot(root: Path) -> dict[str, tuple[str, int]]:
    return {
        str(path.relative_to(root)): (
            f"-> {os.readlink(path)}" if path.is_symlink() else path.read_text(),
            path.lstat().st_mtime_ns,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file() or path.is_symlink()
    }


@pytest.fixture
def toolkit_root(tmp_path: Path) -> Path:
    root = tmp_path / "toolkit"
    (root / "scripts").mkdir(parents=True)
    write_skill(
        root / "skills" / "sync-rules",
        "sync-rules",
        "Sync prose rules with their automated checks in lint-rules.",
    )
    (root / "skills" / "sync-rules" / "references").mkdir()
    (root / "skills" / "sync-rules" / "references" / "principles.md").write_text(
        "# Principles\n"
    )
    write_skill(
        root / "skills" / "reflect-rules",
        "reflect-rules",
        "Mine the active transcript for durable learnings and turn them into rules.",
    )
    write_skill(
        root / "skills" / "correct-rules",
        "correct-rules",
        "Find the mistakes that keep repeating and make each one impossible.",
    )
    write_skill(
        root / "skills" / "setup-mstack", "setup-mstack", "Never installed itself."
    )
    shutil.copytree(
        KNOWN_OVERLAPS,
        root / ".claude" / "skills" / "setup-mstack" / "references",
    )
    return root


@pytest.fixture
def home_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("MSTACK_HOME", raising=False)
    return home


@pytest.fixture
def claude_skills(home_directory: Path) -> Path:
    return home_directory / ".claude" / "skills"


@pytest.fixture
def cursor_skills(home_directory: Path) -> Path:
    return home_directory / ".cursor" / "skills"


@pytest.fixture
def setup_module(
    toolkit_root: Path,
    # Requested only so HOME points at the sandbox before the module loads.
    home_directory: Path,  # pylint: disable=unused-argument
    monkeypatch: pytest.MonkeyPatch,
):
    specification = importlib.util.spec_from_file_location(
        "setup_cli_skills", REPOSITORY_ROOT / "scripts" / "setup.py"
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module, "REPOSITORY_ROOT", toolkit_root)
    monkeypatch.setattr(module, "SKILLS_SOURCE", toolkit_root / "skills")
    return module


@pytest.fixture
def work_directory(tmp_path: Path) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    return work


@pytest.fixture
def plan_skills(setup_module, capsys: pytest.CaptureFixture[str], work_directory: Path):
    def plan(tools: str = "claude") -> dict[str, Any]:
        capsys.readouterr()
        assert setup_module.main(["skills", "plan", "--tools", tools, "--json"]) == 0
        output = capsys.readouterr().out
        (work_directory / "plan.json").write_text(output)
        result: dict[str, Any] = json.loads(output)
        return result

    return plan


@pytest.fixture
def apply_skills(
    setup_module, capsys: pytest.CaptureFixture[str], work_directory: Path
):
    def apply(decisions: dict[str, str], *flags: str) -> int:
        (work_directory / "decisions.json").write_text(json.dumps(decisions))
        capsys.readouterr()
        status: int = setup_module.main([
            "skills",
            "apply",
            "--plan",
            str(work_directory / "plan.json"),
            "--decisions",
            str(work_directory / "decisions.json"),
            "--json",
            *flags,
        ])
        return status

    return apply


@pytest.fixture
def install_everything(plan_skills, apply_skills) -> Callable[[str], dict[str, Any]]:
    def install(tools: str = "claude") -> dict[str, Any]:
        plan = plan_skills(tools)
        assert apply_skills(dict.fromkeys(SKILL_NAMES, "install")) == 0
        return plan

    return install


@pytest.fixture
def actions() -> Callable[[dict[str, Any]], dict[str, str]]:
    def by_id(plan: dict[str, Any]) -> dict[str, str]:
        return {item["id"]: item["action"] for item in plan["items"]}

    return by_id


@pytest.fixture
def toolkit_resolver() -> str:
    text = (
        REPOSITORY_ROOT
        / "skills"
        / "sync-rules"
        / "references"
        / "authoring-a-check.md"
    ).read_text()
    blocks = text.split("```bash\n")[1:]
    snippet = next(block for block in blocks if block.startswith("# resolve-toolkit"))
    return snippet.split("```", 1)[0]
