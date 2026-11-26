import re
from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT

MOVED_COMMAND = re.compile(
    r"(\bmstack|\$\(MSTACK\)) (lint|coverage|domain-check|exceptions|commit-msg"
    r"|hook|init|config|packs)\b"
)
FOLDERS = ("skills", "settings", "docs", ".agents", ".github", "hooks")
FILES = sorted(
    path
    for folder in FOLDERS
    for path in (REPOSITORY_ROOT / folder).rglob("*")
    if path.is_file() and "__pycache__" not in path.parts
) + [
    REPOSITORY_ROOT / name
    for name in ("Makefile", "README.md", "AGENTS.md", "src/mstack/README.md")
]


@pytest.mark.parametrize(
    "path", FILES, ids=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix()
)
def test_file_runs_moved_commands_through_rulepack_when_it_names_one(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")

    assert MOVED_COMMAND.findall(text) == []
