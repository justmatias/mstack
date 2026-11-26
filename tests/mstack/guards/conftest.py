import json
import shutil
from pathlib import Path

import pytest

from mstack.guards.check_skills import find_skills
from tests.conftest import REPOSITORY_ROOT


@pytest.fixture
def skills_sandbox(tmp_path: Path) -> Path:
    """The repo's skills copied flat, the way they are installed."""
    skills, _ = find_skills([REPOSITORY_ROOT / "skills"])
    for skill in skills:
        shutil.copytree(skill, tmp_path / "skills" / skill.name)
    return tmp_path / "skills"


@pytest.fixture
def edit_skill(skills_sandbox: Path):
    def edit(relative_path: str, old: str, new: str) -> None:
        path = skills_sandbox / relative_path
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} not found in {relative_path}"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    return edit


RULE_BODY = "language: Python\nseverity: error\nrule:\n  kind: pass_statement\n"


@pytest.fixture
def lint_sandbox(tmp_path: Path) -> Path:
    """A copy of the repo's lint/ folder: its sgconfig, rules and rule tests."""
    destination = tmp_path / "lint"
    shutil.copytree(REPOSITORY_ROOT / "lint", destination)
    return destination


@pytest.fixture
def write_lint_file(lint_sandbox: Path):
    def write(relative_path: str, content: str) -> Path:
        path = lint_sandbox / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    return write


@pytest.fixture
def write_rule(write_lint_file):
    def write(rule_id: str, relative_path: str | None = None) -> Path:
        return write_lint_file(
            relative_path or f"rules/{rule_id}.yml", f"id: {rule_id}\n{RULE_BODY}"
        )

    return write


@pytest.fixture
def rule_test_issues(run_mstack, lint_sandbox: Path):
    """Run rule-tests-check --json on the sandbox: its exit code and (kind, rule) pairs."""

    def run() -> tuple[int, list[tuple[str, str]]]:
        completed = run_mstack(
            "rule-tests-check",
            "--sgconfig",
            str(lint_sandbox / "sgconfig.yml"),
            "--json",
        )
        issues = json.loads(completed.stdout)["issues"]
        return completed.returncode, [
            (issue["kind"], issue["rule"]) for issue in issues
        ]

    return run


@pytest.fixture(
    params=[
        ("invalid:\n  - pass\n", "missing-valid-cases"),
        ("valid:\n  - x = 1\n", "missing-invalid-cases"),
    ],
    ids=["no-valid-case", "no-invalid-case"],
)
def one_sided_rule_test_kind(request, write_rule, write_lint_file) -> str:
    """Write a rule whose test has only one side; return the issue kind it causes."""
    cases, expected_kind = request.param
    write_rule("no-pass-statement")
    write_lint_file(
        "rule-tests/no-pass-statement-test.yml", f"id: no-pass-statement\n{cases}"
    )
    return expected_kind
