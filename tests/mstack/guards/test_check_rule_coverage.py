import json
from pathlib import Path

import pytest


def test_repository_rules_are_covered(run_mstack):
    completed = run_mstack("coverage")

    assert completed.returncode == 0, completed.stderr


@pytest.mark.usefixtures("_delete_enforced_by_line")
def test_deleting_enforced_by_line_fails(run_mstack, rules_sandbox: Path):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 1
    assert [
        (issue["kind"], issue["check"])
        for issue in json.loads(completed.stdout)["issues"]
    ] == [("unlisted-check", "no-swallowed-exception")]


@pytest.mark.usefixtures("_delete_checks_section")
def test_missing_checks_section_fails(run_mstack, rules_sandbox: Path):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "missing-checks-section"
    ]


@pytest.mark.usefixtures("_add_unknown_check")
def test_unknown_check_fails(run_mstack, rules_sandbox: Path):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "unknown-check"
    ]


@pytest.mark.usefixtures("_point_rule_to_missing_source")
def test_missing_source_fails(run_mstack, rules_sandbox: Path):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "missing-source"
    ]


@pytest.fixture
def import_linter_layout(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "layers.mdc").write_text(
        "# Layers\n\n- The core does not import adapters.\n\n"
        "## Checks\n- enforced-by: core-is-pure\n",
        encoding="utf-8",
    )
    (tmp_path / "sgconfig.yml").write_text("ruleDirs: []\n", encoding="utf-8")
    (tmp_path / ".importlinter").write_text(
        "[importlinter]\nroot_package = app\n\n"
        "[importlinter:contract:core-is-pure]\nname = core-is-pure\n"
        "type = forbidden\nsource_modules = app.core\nforbidden_modules = app.adapters\n",
        encoding="utf-8",
    )
    return tmp_path


def coverage_arguments(layout: Path) -> list[str]:
    return [
        "--rules-dir",
        str(layout / "rules"),
        "--config",
        str(layout / "sgconfig.yml"),
        "--importlinter",
        str(layout / ".importlinter"),
        "--json",
    ]


def test_import_linter_contract_counts_as_check(run_mstack, import_linter_layout: Path):
    completed = run_mstack(
        "coverage",
        *coverage_arguments(import_linter_layout),
        working_directory=import_linter_layout,
    )

    assert completed.returncode == 0, completed.stdout
    assert json.loads(completed.stdout)["rules"][0]["checks"] == ["core-is-pure"]


def test_removed_import_linter_contract_is_unknown_check(
    run_mstack, import_linter_layout: Path
):
    (import_linter_layout / ".importlinter").write_text(
        "[importlinter]\nroot_package = app\n", encoding="utf-8"
    )

    completed = run_mstack(
        "coverage",
        *coverage_arguments(import_linter_layout),
        working_directory=import_linter_layout,
    )

    assert completed.returncode == 1
    assert [
        (issue["kind"], issue["check"])
        for issue in json.loads(completed.stdout)["issues"]
    ] == [("unknown-check", "core-is-pure")]
