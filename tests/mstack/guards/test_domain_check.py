from pathlib import Path


def test_domain_check_passes_when_repository_rules_are_generic(run_mstack):
    completed = run_mstack("domain-check")

    assert completed.returncode == 0, completed.stderr


def test_domain_check_fails_when_rule_names_a_repo_identifier(
    run_mstack, leaking_rule: Path
):
    completed = run_mstack("domain-check", str(leaking_rule))

    assert completed.returncode == 1
    assert "repo identifier 'InMemoryOrderRepository'" in completed.stderr
    assert f"{leaking_rule}:3" in completed.stderr


def test_domain_check_fails_when_rule_has_url_and_email(
    run_mstack, rule_with_url_and_email: Path
):
    completed = run_mstack("domain-check", str(rule_with_url_and_email))

    assert completed.returncode == 1
    assert "URL 'https://wiki.internal.corp/page'" in completed.stderr
    assert "email 'someone@internal-team.example.com'" in completed.stderr
