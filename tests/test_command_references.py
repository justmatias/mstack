import re
from pathlib import Path

# coverage, domain-check, exceptions and commit-msg moved back: rulepack v0.7.0
# dropped them, and they run as `mstack <command>`.
MOVED_COMMAND = re.compile(r"(\bmstack|\$\(MSTACK\)) (lint|hook|init|config|packs)\b")


def test_file_runs_moved_commands_through_rulepack_when_it_names_one(
    command_reference_file: Path,
):
    text = command_reference_file.read_text(encoding="utf-8", errors="replace")

    assert MOVED_COMMAND.findall(text) == []
