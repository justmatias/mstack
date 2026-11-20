from pathlib import Path


def test_example_rules_pass(run_mstack):
    completed = run_mstack("domain-check")

    assert completed.returncode == 0, completed.stderr


def test_repo_identifier_is_caught(run_mstack, leaking_rule: Path):
    completed = run_mstack("domain-check", str(leaking_rule))

    assert completed.returncode == 1
    assert "repo identifier 'InMemoryOrderRepository'" in completed.stderr
    assert f"{leaking_rule}:3" in completed.stderr


def test_url_and_email_are_caught(run_mstack, rule_with_url_and_email: Path):
    completed = run_mstack("domain-check", str(rule_with_url_and_email))

    assert completed.returncode == 1
    assert "URL 'https://wiki.internal.corp/page'" in completed.stderr
    assert "email 'someone@internal-team.example.com'" in completed.stderr
