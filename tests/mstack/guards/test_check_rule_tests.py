from pathlib import Path


def test_rule_tests_check_passes_when_every_repository_rule_is_tested(run_mstack):
    completed = run_mstack("rule-tests-check")

    assert completed.returncode == 0, completed.stderr
    assert "each tested" in completed.stderr


def test_rule_tests_check_fails_when_rule_has_no_test(
    rule_test_issues, lint_sandbox: Path
):
    (lint_sandbox / "rule-tests" / "no-bare-except-test.yml").unlink()

    assert rule_test_issues() == (1, [("untested-rule", "no-bare-except")])


def test_rule_tests_check_reads_rule_when_it_is_in_a_subfolder(
    rule_test_issues, write_rule
):
    write_rule("no-pass-statement", "rules/nested/no-pass-statement.yml")

    assert rule_test_issues() == (1, [("untested-rule", "no-pass-statement")])


def test_rule_tests_check_fails_when_rule_test_lacks_a_side(
    rule_test_issues, one_sided_rule_test_kind: str
):
    assert rule_test_issues() == (1, [(one_sided_rule_test_kind, "no-pass-statement")])


def test_rule_tests_check_fails_when_rule_test_names_no_rule(
    rule_test_issues, write_lint_file
):
    write_lint_file(
        "rule-tests/no-such-rule-test.yml",
        "id: no-such-rule\nvalid:\n  - x = 1\ninvalid:\n  - pass\n",
    )

    assert rule_test_issues() == (1, [("unknown-rule-test", "no-such-rule")])


def test_rule_tests_check_fails_when_two_rule_files_share_an_id(
    rule_test_issues, write_rule
):
    write_rule("no-bare-except", "rules/no-bare-except-copy.yml")

    assert rule_test_issues() == (1, [("duplicate-rule-id", "no-bare-except")])


def test_rule_tests_check_exits_with_message_when_sgconfig_is_missing(
    run_mstack, tmp_path: Path
):
    completed = run_mstack(
        "rule-tests-check", "--sgconfig", str(tmp_path / "sgconfig.yml")
    )

    assert completed.returncode == 2
    assert "no ast-grep config" in completed.stderr


def test_rule_tests_check_exits_with_message_when_rule_file_is_invalid_yaml(
    run_mstack, lint_sandbox: Path, write_lint_file
):
    write_lint_file("rules/broken.yml", "id: [unclosed\n")

    completed = run_mstack(
        "rule-tests-check", "--sgconfig", str(lint_sandbox / "sgconfig.yml")
    )

    assert completed.returncode == 2
    assert "broken.yml: invalid YAML" in completed.stderr
