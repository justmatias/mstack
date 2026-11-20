import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SGCONFIG = REPOSITORY_ROOT / "lint" / "sgconfig.yml"


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


@pytest.fixture
def run_resolver(toolkit_resolver: str, tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)

    def run(**variables: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", "-c", toolkit_resolver],
            env={"HOME": str(home), "PATH": "/usr/bin:/bin", **variables},
            capture_output=True,
            text=True,
            check=False,
        )

    return run


@pytest.fixture
def toolkit_config(tmp_path: Path) -> Path:
    config = tmp_path / "home" / ".config" / "mstack" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"toolkit_path": str(REPOSITORY_ROOT)}))
    return config
