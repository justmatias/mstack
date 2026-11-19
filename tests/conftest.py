import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SGCONFIG = REPOSITORY_ROOT / "lint-rules" / "sgconfig.yml"


@pytest.fixture
def repository_root() -> Path:
    return REPOSITORY_ROOT


@pytest.fixture
def scan_findings():
    def scan(*paths: Path) -> list[dict]:
        completed = subprocess.run(
            [
                "ast-grep",
                "scan",
                "-c",
                str(SGCONFIG),
                "--json=stream",
                *[str(path) for path in paths],
            ],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return [json.loads(line) for line in completed.stdout.splitlines() if line]

    return scan


@pytest.fixture
def import_linter_sandbox(tmp_path: Path) -> Path:
    shutil.copytree(
        REPOSITORY_ROOT / "fixtures" / "valid", tmp_path / "fixtures" / "valid"
    )
    shutil.copy(
        REPOSITORY_ROOT / "fixtures" / "__init__.py",
        tmp_path / "fixtures" / "__init__.py",
    )
    shutil.copy(REPOSITORY_ROOT / ".importlinter", tmp_path / ".importlinter")
    return tmp_path


@pytest.fixture
def run_lint_imports():
    def run(working_directory: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["lint-imports"],
            cwd=working_directory,
            capture_output=True,
            text=True,
            check=False,
        )

    return run


def read_frontmatter(path: Path) -> dict:
    _, frontmatter, _ = path.read_text(encoding="utf-8").split("---", 2)
    data: dict = yaml.safe_load(frontmatter)
    return data
