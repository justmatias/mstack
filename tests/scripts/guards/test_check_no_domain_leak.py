from pathlib import Path


def test_example_rules_pass(run_guard):
    completed = run_guard(
        "check_no_domain_leak",
        "lint-rules",
        ".cursor/rules",
        "--repo",
        ".",
        "--exclude",
        "scripts",
        "--exclude",
        "tests",
        "--exclude",
        "fixtures/invalid",
    )

    assert completed.returncode == 0, completed.stderr


def test_repo_identifier_is_caught(run_guard, leaking_rule: Path):
    completed = run_guard(
        "check_no_domain_leak",
        str(leaking_rule),
        "--repo",
        ".",
        "--exclude",
        "scripts",
        "--exclude",
        "tests",
        "--exclude",
        "fixtures/invalid",
    )

    assert completed.returncode == 1
    assert "repo identifier 'InMemoryOrderRepository'" in completed.stderr
    assert f"{leaking_rule}:3" in completed.stderr


def test_url_and_email_are_caught(run_guard, rule_with_url_and_email: Path):
    completed = run_guard(
        "check_no_domain_leak",
        str(rule_with_url_and_email),
        "--repo",
        ".",
        "--exclude",
        "scripts",
        "--exclude",
        "tests",
        "--exclude",
        "fixtures/invalid",
    )

    assert completed.returncode == 1
    assert "URL 'https://wiki.internal.corp/page'" in completed.stderr
    assert "email 'someone@internal-team.example.com'" in completed.stderr
