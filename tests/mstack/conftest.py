import sys
from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT, run_command


@pytest.fixture
def run_mstack():
    def run(command: str, *arguments: str, working_directory: Path = REPOSITORY_ROOT):
        return run_command(
            [sys.executable, "-m", "mstack", command, *arguments], working_directory
        )

    return run


@pytest.fixture
def git_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    return repository


@pytest.fixture
def write_config(git_repository: Path):
    def write(content: str, name: str = ".mstack.toml") -> Path:
        path = git_repository / name
        path.write_text(content, encoding="utf-8")
        return path

    return write
