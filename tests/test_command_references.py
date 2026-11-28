import re
from pathlib import Path

# coverage moved back: rulepack v0.7.0 dropped it, and it runs as `mstack coverage`.
MOVED_COMMAND = re.compile(r"(\bmstack|\$\(MSTACK\)) (lint|hook|init|config|packs)\b")
MOVED_BACK_COMMAND = re.compile(r"(\brulepack|\$\(RULEPACK\)) coverage\b")


def test_file_runs_moved_commands_through_rulepack_when_it_names_one(
    command_reference_file: Path,
):
    text = command_reference_file.read_text(encoding="utf-8", errors="replace")

    assert MOVED_COMMAND.findall(text) == []
    assert MOVED_BACK_COMMAND.findall(text) == []
