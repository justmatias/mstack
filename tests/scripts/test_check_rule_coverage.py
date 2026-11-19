import json
from pathlib import Path

import pytest


def test_repository_rules_are_covered(run_script):
    completed = run_script("check_rule_coverage.py")

    assert completed.returncode == 0, completed.stderr


@pytest.mark.usefixtures("_delete_enforced_by_line")
def test_deleting_enforced_by_line_fails(run_script, rules_sandbox: Path):
    completed = run_script(
        "check_rule_coverage.py", "--json", working_directory=rules_sandbox
    )

    assert completed.returncode == 1
    assert [
        (issue["kind"], issue["check"])
        for issue in json.loads(completed.stdout)["issues"]
    ] == [("unlisted-check", "no-manual-init-boilerplate")]


@pytest.mark.usefixtures("_delete_checks_section")
def test_missing_checks_section_fails(run_script, rules_sandbox: Path):
    completed = run_script(
        "check_rule_coverage.py", "--json", working_directory=rules_sandbox
    )

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "missing-checks-section"
    ]


@pytest.mark.usefixtures("_add_unknown_check")
def test_unknown_check_fails(run_script, rules_sandbox: Path):
    completed = run_script(
        "check_rule_coverage.py", "--json", working_directory=rules_sandbox
    )

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "unknown-check"
    ]


@pytest.mark.usefixtures("_point_rule_to_missing_source")
def test_missing_source_fails(run_script, rules_sandbox: Path):
    completed = run_script(
        "check_rule_coverage.py", "--json", working_directory=rules_sandbox
    )

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "missing-source"
    ]
