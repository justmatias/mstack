import json
from pathlib import Path

from mstack.doctor import main


def statuses(results) -> dict[tuple[str, str], str]:
    return {(result.group, result.check): result.status for result in results}


def append_line(path: Path) -> None:
    path.write_text(path.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")


def drift_rows(results) -> list[tuple[str, str]]:
    return [(result.check, result.status) for result in results]


def run_doctor(capsys, *arguments: str) -> tuple[int, dict]:
    exit_code = main(["--json", *arguments])
    return exit_code, json.loads(capsys.readouterr().out)
