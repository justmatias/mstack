import json
import sys
from pathlib import Path

import pytest

from tests.helpers import run_command

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SGCONFIG = REPOSITORY_ROOT / "lint" / "sgconfig.yml"
# The files that tell users or agents which commands to run.
COMMAND_REFERENCE_FOLDERS = (
    "skills",
    "settings",
    "docs",
    ".agents",
    ".github",
    "hooks",
)
COMMAND_REFERENCE_FILES = sorted(
    path
    for folder in COMMAND_REFERENCE_FOLDERS
    for path in (REPOSITORY_ROOT / folder).rglob("*")
    if path.is_file() and "__pycache__" not in path.parts
) + [
    REPOSITORY_ROOT / name
    for name in ("Makefile", "README.md", "AGENTS.md", "src/mstack/README.md")
]


@pytest.fixture(
    params=COMMAND_REFERENCE_FILES,
    ids=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix(),
)
def command_reference_file(request) -> Path:
    return request.param


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
