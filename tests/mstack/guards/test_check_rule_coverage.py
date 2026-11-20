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


def coverage_issues(run_mstack, rules_sandbox: Path) -> tuple[int, list[tuple]]:
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)
    issues = json.loads(completed.stdout)["issues"]
    return completed.returncode, [
        (issue["kind"], issue.get("check")) for issue in issues
    ]


@pytest.mark.usefixtures("pre_commit_config")
@pytest.mark.parametrize(
    "hook_id", ["gitleaks", "check-something"], ids=["remote", "local"]
)
def test_configured_hook_counts_as_check(
    run_mstack, rules_sandbox: Path, add_hook_line, hook_id: str
):
    add_hook_line(hook_id)

    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 0, completed.stdout
    logging_rule = next(
        rule
        for rule in json.loads(completed.stdout)["rules"]
        if rule["mdc"].endswith("logging.mdc")
    )
    assert logging_rule["hooks"] == [hook_id]


@pytest.mark.usefixtures("pre_commit_config")
def test_unknown_hook_fails(run_mstack, rules_sandbox: Path, add_hook_line):
    add_hook_line("no-such-hook")

    assert coverage_issues(run_mstack, rules_sandbox) == (
        1,
        [("unknown-hook", "no-such-hook")],
    )


def test_missing_pre_commit_config_makes_every_hook_unknown(
    run_mstack, rules_sandbox: Path, add_hook_line
):
    add_hook_line("gitleaks")

    exit_code, issues = coverage_issues(run_mstack, rules_sandbox)

    assert (exit_code, issues) == (1, [("unknown-hook", "gitleaks")])


@pytest.mark.usefixtures("pre_commit_config", "_only_hook_in_checks_section")
def test_checks_section_with_only_hooks_is_not_missing(run_mstack, rules_sandbox: Path):
    assert coverage_issues(run_mstack, rules_sandbox) == (0, [])


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
