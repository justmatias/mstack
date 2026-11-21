import json
from pathlib import Path

import pytest

from tests.mstack.guards.conftest import (
    coverage_arguments,
    coverage_issues,
    credit_rule,
)


def test_repository_rules_are_covered(run_mstack):
    completed = run_mstack("coverage")

    assert completed.returncode == 0, completed.stderr


def test_coverage_passes_when_a_check_has_no_prose_source(
    run_mstack, rules_sandbox: Path
):
    (rules_sandbox / "lint" / "rules" / "no-placeholder.yml").write_text(
        "id: no-placeholder\nlanguage: Python\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )

    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 0, completed.stdout


@pytest.mark.usefixtures("_add_unlisted_check")
def test_coverage_fails_when_the_source_does_not_list_the_check(
    run_mstack, rules_sandbox: Path
):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 1
    assert [
        (issue["kind"], issue["check"])
        for issue in json.loads(completed.stdout)["issues"]
    ] == [("unlisted-check", "no-linked-placeholder")]


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


@pytest.mark.usefixtures("_add_check_with_missing_source")
def test_missing_source_fails(run_mstack, rules_sandbox: Path):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert [issue["kind"] for issue in json.loads(completed.stdout)["issues"]] == [
        "missing-source"
    ]


# The sandbox has this repo's .pre-commit-config.yaml: gitleaks is a remote hook,
# lint-rules a local one.
@pytest.mark.parametrize("hook_id", ["gitleaks", "lint-rules"], ids=["remote", "local"])
def test_configured_hook_counts_as_check(
    run_mstack, rules_sandbox: Path, add_hook_line, hook_id: str
):
    add_hook_line(hook_id)

    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 0, completed.stdout
    naming_rule = next(
        rule
        for rule in json.loads(completed.stdout)["rules"]
        if rule["mdc"].endswith("naming.mdc")
    )
    assert naming_rule["hooks"] == [hook_id]


def test_unknown_hook_fails(run_mstack, rules_sandbox: Path, add_hook_line):
    add_hook_line("no-such-hook")

    assert coverage_issues(run_mstack, rules_sandbox) == (
        1,
        [("unknown-hook", "no-such-hook")],
    )


def test_missing_pre_commit_config_makes_every_hook_unknown(
    run_mstack, rules_sandbox: Path, add_hook_line
):
    (rules_sandbox / ".pre-commit-config.yaml").unlink()
    add_hook_line("gitleaks")

    exit_code, issues = coverage_issues(run_mstack, rules_sandbox)

    assert exit_code == 1
    assert ("unknown-hook", "gitleaks") in issues
    assert {kind for kind, _ in issues} == {"unknown-hook"}


@pytest.mark.usefixtures("_only_hook_in_checks_section")
def test_checks_section_with_only_hooks_is_not_missing(run_mstack, rules_sandbox: Path):
    assert coverage_issues(run_mstack, rules_sandbox) == (0, [])


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


def test_complete_rule_credit_passes(run_mstack, rules_sandbox: Path):
    credit_rule(
        rules_sandbox,
        "license: MIT\nmetadata:\n"
        '  adapted-from: "rules/naming.mdc in owner/repo"\n'
        f'  upstream-commit: "{"a" * 40}"\n',
    )

    assert coverage_issues(run_mstack, rules_sandbox) == (0, [])


def test_rule_credit_without_upstream_commit_fails(run_mstack, rules_sandbox: Path):
    credit_rule(
        rules_sandbox,
        'license: MIT\nmetadata:\n  adapted-from: "rules/naming.mdc in owner/repo"\n',
    )

    assert coverage_issues(run_mstack, rules_sandbox) == (1, [("credit", None)])


def test_rule_license_without_adapted_from_fails(run_mstack, rules_sandbox: Path):
    credit_rule(rules_sandbox, "license: MIT\n")

    assert coverage_issues(run_mstack, rules_sandbox) == (1, [("credit", None)])
