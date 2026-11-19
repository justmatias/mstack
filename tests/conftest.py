import json
import shutil
import subprocess
from pathlib import Path

import pytest

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
    shutil.copytree(REPOSITORY_ROOT / "example_app", tmp_path / "example_app")
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
