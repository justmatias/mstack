import shutil
from pathlib import Path

import pytest

from mstack.guards.check_skills import find_skills
from tests.conftest import REPOSITORY_ROOT


@pytest.fixture
def skills_sandbox(tmp_path: Path) -> Path:
    """The repo's skills copied flat, the way they are installed."""
    skills, _ = find_skills([REPOSITORY_ROOT / "skills"])
    for skill in skills:
        shutil.copytree(skill, tmp_path / "skills" / skill.name)
    return tmp_path / "skills"


@pytest.fixture
def edit_skill(skills_sandbox: Path):
    def edit(relative_path: str, old: str, new: str) -> None:
        path = skills_sandbox / relative_path
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} not found in {relative_path}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    return edit
