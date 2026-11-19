from pathlib import Path


def test_example_rules_pass(run_script):
    completed = run_script(
        "check_no_domain_leak.py",
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


def test_repo_identifier_is_caught(run_script, leaking_rule: Path):
    completed = run_script(
        "check_no_domain_leak.py",
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


def test_url_and_email_are_caught(run_script, rule_with_url_and_email: Path):
    completed = run_script(
        "check_no_domain_leak.py",
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
