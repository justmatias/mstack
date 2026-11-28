import json
from pathlib import Path

import pytest


def test_coverage_passes_when_repository_rules_are_complete(run_mstack):
    completed = run_mstack("coverage")

    assert completed.returncode == 0, completed.stderr


def test_coverage_reads_rules_dir_when_mstack_config_sets_it(coverage_issues):
    exit_code, issues = coverage_issues()

    assert (exit_code, issues) == (0, [])


def test_coverage_passes_when_a_check_has_no_prose_source(
    coverage_issues, rules_sandbox: Path
):
    (rules_sandbox / "lint" / "rules" / "no-placeholder.yml").write_text(
        "id: no-placeholder\nlanguage: Python\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )

    assert coverage_issues() == (0, [])


def test_coverage_fails_when_rules_and_checks_disagree(
    coverage_issues, broken_coverage_issue: tuple[str, str | None]
):
    assert coverage_issues() == (1, [broken_coverage_issue])


def test_coverage_counts_hook_as_check_when_it_is_configured(
    run_mstack, rules_sandbox: Path, configured_hook_id: str
):
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)

    assert completed.returncode == 0, completed.stdout
    naming = next(
        rule
        for rule in json.loads(completed.stdout)["rules"]
        if rule["mdc"].endswith("naming.mdc")
    )
    assert naming["hooks"] == [configured_hook_id]


def test_coverage_fails_when_hook_is_unknown(coverage_issues, add_hook_line):
    add_hook_line("no-such-hook")

    assert coverage_issues() == (1, [("unknown-hook", "no-such-hook")])


def test_coverage_reports_every_hook_unknown_when_pre_commit_config_is_missing(
    coverage_issues, rules_sandbox: Path, add_hook_line
):
    (rules_sandbox / ".pre-commit-config.yaml").unlink()
    add_hook_line("gitleaks")

    exit_code, issues = coverage_issues()

    assert exit_code == 1
    assert ("unknown-hook", "gitleaks") in issues
    assert {kind for kind, _ in issues} == {"unknown-hook"}


def test_coverage_counts_contract_as_check_when_import_linter_defines_it(
    layout_coverage,
):
    exit_code, report = layout_coverage()

    assert exit_code == 0, report
    assert report["rules"][0]["checks"] == ["core-is-pure"]


def test_coverage_fails_when_import_linter_contract_is_removed(
    layout_coverage, import_linter_layout: Path
):
    (import_linter_layout / ".importlinter").write_text(
        "[importlinter]\nroot_package = app\n", encoding="utf-8"
    )

    exit_code, report = layout_coverage()

    assert exit_code == 1
    assert [(issue["kind"], issue["check"]) for issue in report["issues"]] == [
        ("unknown-check", "core-is-pure")
    ]


def test_coverage_passes_when_rule_credit_is_complete(coverage_issues, credit_rule):
    credit_rule(
        "license: MIT\nmetadata:\n"
        '  adapted-from: "rules/naming.mdc in owner/repo"\n'
        f'  upstream-commit: "{"a" * 40}"\n'
    )

    assert coverage_issues() == (0, [])


def test_coverage_fails_when_rule_credit_has_no_upstream_commit(
    coverage_issues, credit_rule
):
    credit_rule(
        'license: MIT\nmetadata:\n  adapted-from: "rules/naming.mdc in owner/repo"\n'
    )

    assert coverage_issues() == (1, [("credit", None)])


@pytest.mark.usefixtures("_write_invalid_guard_config")
def test_coverage_exits_with_config_error_when_mstack_config_is_invalid(
    run_mstack, rules_sandbox: Path
):
    completed = run_mstack("coverage", working_directory=rules_sandbox)

    assert completed.returncode == 2
    assert "invalid TOML" in completed.stderr
