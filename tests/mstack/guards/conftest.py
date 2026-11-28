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


GUARD_SAMPLE_PATHS = (
    "rules",
    "lint",
    ".pre-commit-config.yaml",
    ".rulepack.toml",
    ".mstack.toml",
)


@pytest.fixture
def rules_sandbox(tmp_path: Path) -> Path:
    """A repo with this repo's prose rules, checks and both config files."""
    sandbox = tmp_path / "sandbox"
    (sandbox / ".git").mkdir(parents=True)
    for name in GUARD_SAMPLE_PATHS:
        source = REPOSITORY_ROOT / name
        if source.is_dir():
            shutil.copytree(source, sandbox / name)
        else:
            shutil.copy2(source, sandbox / name)
    return sandbox


@pytest.fixture
def naming_rule(rules_sandbox: Path) -> Path:
    return rules_sandbox / "rules" / "naming.mdc"


@pytest.fixture
def coverage_issues(run_mstack, rules_sandbox: Path):
    """Run coverage --json in the sandbox: its exit code and (kind, check) pairs."""

    def run() -> tuple[int, list[tuple[str, str | None]]]:
        completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)
        issues = json.loads(completed.stdout)["issues"]
        return completed.returncode, [
            (issue["kind"], issue.get("check")) for issue in issues
        ]

    return run


@pytest.fixture
def _add_unlisted_check(rules_sandbox: Path) -> None:
    (rules_sandbox / "rules" / "linked.mdc").write_text(
        "# Linked rule\n\n## Checks\n- enforcement: llm-review\n", encoding="utf-8"
    )
    (rules_sandbox / "lint" / "rules" / "no-linked-placeholder.yml").write_text(
        "id: no-linked-placeholder\nlanguage: Python\n"
        "metadata:\n  source: rules/linked.mdc\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )


@pytest.fixture
def _delete_checks_section(naming_rule: Path) -> None:
    naming_rule.write_text(
        naming_rule.read_text(encoding="utf-8").split("## Checks")[0],
        encoding="utf-8",
    )


@pytest.fixture
def _add_unknown_check(naming_rule: Path) -> None:
    with naming_rule.open("a", encoding="utf-8") as rule:
        rule.write("- enforced-by: no-such-check\n")


@pytest.fixture
def _add_check_with_missing_source(rules_sandbox: Path) -> None:
    (rules_sandbox / "lint" / "rules" / "no-linked-placeholder.yml").write_text(
        "id: no-linked-placeholder\nlanguage: Python\n"
        "metadata:\n  source: rules/missing.mdc\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )


@pytest.fixture(
    params=[
        ("_add_unlisted_check", "unlisted-check", "no-linked-placeholder"),
        ("_delete_checks_section", "missing-checks-section", None),
        ("_add_unknown_check", "unknown-check", "no-such-check"),
        ("_add_check_with_missing_source", "missing-source", "no-linked-placeholder"),
    ],
    ids=["unlisted-check", "no-checks-section", "unknown-check", "missing-source"],
)
def broken_coverage_issue(request) -> tuple[str, str | None]:
    """Break the sandbox's coverage one way; return the (kind, check) it causes."""
    breakage, kind, check = request.param
    request.getfixturevalue(breakage)
    return kind, check


@pytest.fixture
def add_hook_line(naming_rule: Path):
    def add(hook_id: str) -> None:
        with naming_rule.open("a", encoding="utf-8") as rule:
            rule.write(f"- enforced-by-hook: {hook_id}\n")

    return add


# The sandbox has this repo's .pre-commit-config.yaml: gitleaks is a remote hook,
# lint-rules a local one.
@pytest.fixture(params=["gitleaks", "lint-rules"], ids=["remote", "local"])
def configured_hook_id(request, add_hook_line) -> str:
    add_hook_line(request.param)
    return request.param


@pytest.fixture
def credit_rule(naming_rule: Path):
    def write(credit: str) -> None:
        text = naming_rule.read_text(encoding="utf-8")
        naming_rule.write_text(
            text.replace("---\n", f"---\n{credit}", 1), encoding="utf-8"
        )

    return write


@pytest.fixture
def import_linter_layout(tmp_path: Path) -> Path:
    layout = tmp_path / "layout"
    (layout / ".git").mkdir(parents=True)
    (layout / "rules").mkdir()
    (layout / "rules" / "layers.mdc").write_text(
        "# Layers\n\n- The core does not import adapters.\n\n"
        "## Checks\n- enforced-by: core-is-pure\n",
        encoding="utf-8",
    )
    (layout / "sgconfig.yml").write_text("ruleDirs: []\n", encoding="utf-8")
    (layout / ".importlinter").write_text(
        "[importlinter]\nroot_package = app\n\n"
        "[importlinter:contract:core-is-pure]\nname = core-is-pure\n"
        "type = forbidden\nsource_modules = app.core\nforbidden_modules = app.adapters\n",
        encoding="utf-8",
    )
    return layout


@pytest.fixture
def layout_coverage(run_mstack, import_linter_layout: Path):
    """Run coverage --json on the import-linter layout, with every path as a flag."""

    def run() -> tuple[int, dict]:
        completed = run_mstack(
            "coverage",
            "--rules-dir",
            str(import_linter_layout / "rules"),
            "--config",
            str(import_linter_layout / "sgconfig.yml"),
            "--importlinter",
            str(import_linter_layout / ".importlinter"),
            "--json",
            working_directory=import_linter_layout,
        )
        return completed.returncode, json.loads(completed.stdout)

    return run


VALID_EXCEPTION = (
    '# rule-exception: reason="third-party legacy API" expires=2999-12-31 '
    "approved-by=@reviewer\n"
)
SHELL_SOURCE = (
    "#!/usr/bin/env bash\nset -euo pipefail\n"
    '{header}# ast-grep-ignore: no-eval\neval "$1"\n'
)
PYTHON_SOURCE = (
    "{header}# ast-grep-ignore: no-manual-init-boilerplate\n"
    "class Foo:\n    def __init__(self, name):\n        self.name = name\n"
)


@pytest.fixture(
    params=[("module.py", PYTHON_SOURCE), ("task.sh", SHELL_SOURCE)],
    ids=["python", "shell"],
)
def exception_file(request, tmp_path: Path):
    """Write a file whose ast-grep-ignore has the given rule-exception header."""
    name, template = request.param

    def write(header: str) -> Path:
        path = tmp_path / name
        path.write_text(template.format(header=header), encoding="utf-8")
        return path

    return write


@pytest.fixture
def justified_exception_file(exception_file) -> Path:
    return exception_file(VALID_EXCEPTION)


@pytest.fixture(
    params=[
        ("", "needs a '# rule-exception:'"),
        (
            '# rule-exception: reason="legacy" expires=2000-01-01 approved-by=@reviewer\n',
            "expired on 2000-01-01",
        ),
        (
            '# rule-exception: reason="legacy" expires=2999-12-31\n',
            "missing approved-by",
        ),
        (
            "# rule-exception: expires=2999-12-31 approved-by=@reviewer\n",
            "missing reason",
        ),
        (
            '# rule-exception: reason="legacy" expires=someday approved-by=@reviewer\n',
            "not a YYYY-MM-DD date",
        ),
    ],
    ids=["no-justification", "expired", "no-approval", "no-reason", "bad-date"],
)
def unjustified_exception(request, exception_file) -> tuple[Path, str]:
    """A file with a broken rule-exception, and the problem it reports."""
    header, problem = request.param
    return exception_file(header), problem


@pytest.fixture
def leaking_rule(tmp_path: Path) -> Path:
    path = tmp_path / "leaking-rule.yml"
    path.write_text(
        "id: no-direct-repository\n"
        "language: Python\n"
        "message: Do not instantiate InMemoryOrderRepository directly\n"
        "rule:\n"
        "  pattern: InMemoryOrderRepository()\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def rule_with_url_and_email(tmp_path: Path) -> Path:
    path = tmp_path / "contact-rule.yml"
    path.write_text(
        "note: |\n"
        "  Ask someone@internal-team.example.com or see https://wiki.internal.corp/page\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def commit_message(run_mstack, rules_sandbox: Path):
    """Run commit-msg on a message inside the sandbox, which has its own config."""

    def check(message: str):
        path = rules_sandbox / "COMMIT_EDITMSG"
        path.write_text(message, encoding="utf-8")
        return run_mstack("commit-msg", str(path), working_directory=rules_sandbox)

    return check


@pytest.fixture(
    params=[
        "feat: add the shell rules\n",
        "fix(lint): skip the scan when nothing changed\n",
        "refactor(install)!: drop the old manifest schema\n",
        "docs: explain the hooks\n\nThe README only listed the ids, not when each runs.\n",
        "feat: " + "a" * 66 + "\n",
    ],
    ids=["plain", "scope", "breaking", "body", "72-characters"],
)
def valid_commit_message(request) -> str:
    return request.param


@pytest.fixture(
    params=[
        ("feature: add the rules\n", "'feature' is not an allowed type"),
        ("Feat: add the rules\n", "Conventional Commits subject"),
        ("feat:add the rules\n", "Conventional Commits subject"),
        ("feat: " + "a" * 67 + "\n", "73 characters, at most 72"),
        ("feat: add the rules.\n", "no trailing period"),
        ("feat: add the rules\nBecause they were missing.\n", "blank line"),
    ],
    ids=[
        "unknown-type",
        "uppercase-type",
        "missing-space",
        "73-characters",
        "trailing-period",
        "no-blank-line",
    ],
)
def invalid_commit_message(request) -> tuple[str, str]:
    """A message that breaks the rule, and the problem it reports."""
    return request.param


@pytest.fixture(
    params=[
        "Merge branch 'main' into feature\n",
        'Revert "feat: add the rules"\n\nThis reverts commit abc.\n',
        "fixup! feat: add the rules\n",
        "squash! feat: add the rules\n",
    ],
    ids=["merge", "revert", "fixup", "squash"],
)
def generated_commit_message(request) -> str:
    return request.param


@pytest.fixture
def _allow_change_commit_type(rules_sandbox: Path) -> None:
    with (rules_sandbox / ".mstack.toml").open("a", encoding="utf-8") as config:
        config.write('\n[commits]\ntypes = ["change", "fix"]\n')


@pytest.fixture
def _write_invalid_guard_config(rules_sandbox: Path) -> None:
    (rules_sandbox / ".mstack.toml").write_text("rules_dir = [\n", encoding="utf-8")
