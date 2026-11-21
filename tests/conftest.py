import json
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SGCONFIG = REPOSITORY_ROOT / "lint" / "sgconfig.yml"


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


@pytest.fixture
def repository_root() -> Path:
    return REPOSITORY_ROOT


@pytest.fixture
def scan_findings():
    def scan(*paths: Path) -> list[dict]:
        completed = run_command(
            [
                "ast-grep",
                "scan",
                "-c",
                str(SGCONFIG),
                "--json=stream",
                *[str(path) for path in paths],
            ],
            REPOSITORY_ROOT,
        )
        return [json.loads(line) for line in completed.stdout.splitlines() if line]

    return scan


@pytest.fixture(autouse=True)
def _host_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never resolve the real Windows profile on WSL: tests use a temporary HOME."""
    native = {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")
    monkeypatch.setenv("MSTACK_PLATFORM", native)
    monkeypatch.delenv("MSTACK_WINDOWS_HOME", raising=False)


@pytest.fixture
def repository_with_a_rule(tmp_path: Path) -> Path:
    repository = tmp_path / "target"
    (repository / "lint-rules" / "rules").mkdir(parents=True)
    (repository / "lint-rules" / "sgconfig.yml").write_text("ruleDirs:\n  - rules\n")
    source = REPOSITORY_ROOT / "lint" / "rules" / "no-bare-except.yml"
    (repository / "lint-rules" / "rules" / source.name).write_bytes(source.read_bytes())
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
    return repository


def try_repo(
    repository: Path, source: str, *hook_id: str
) -> subprocess.CompletedProcess:
    (repository / "module.py").write_text(source)
    subprocess.run(["git", "add", "--all"], cwd=repository, check=True)
    return subprocess.run(
        ["pre-commit", "try-repo", str(REPOSITORY_ROOT), *hook_id, "--all-files"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
