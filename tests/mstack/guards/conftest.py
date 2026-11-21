import json
import shutil
from pathlib import Path

import pytest

from mstack.guards.check_skills import find_skills
from tests.conftest import REPOSITORY_ROOT


@pytest.fixture
def rules_sandbox(tmp_path: Path) -> Path:
    shutil.copytree(REPOSITORY_ROOT / "rules", tmp_path / "rules")
    shutil.copytree(REPOSITORY_ROOT / "lint", tmp_path / "lint")
    shutil.copy(REPOSITORY_ROOT / ".mstack.toml", tmp_path / ".mstack.toml")
    shutil.copy(
        REPOSITORY_ROOT / ".pre-commit-config.yaml",
        tmp_path / ".pre-commit-config.yaml",
    )
    return tmp_path


@pytest.fixture
def _add_unlisted_check(rules_sandbox: Path) -> None:
    (rules_sandbox / "rules" / "linked.mdc").write_text(
        "# Linked rule\n\n## Checks\n- enforcement: llm-review\n",
        encoding="utf-8",
    )
    (rules_sandbox / "lint" / "rules" / "no-linked-placeholder.yml").write_text(
        "id: no-linked-placeholder\nlanguage: Python\n"
        "metadata:\n  source: rules/linked.mdc\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )


@pytest.fixture
def _delete_checks_section(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "naming.mdc"
    mdc.write_text(mdc.read_text().split("## Checks")[0])


@pytest.fixture
def _add_unknown_check(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "naming.mdc"
    mdc.write_text(mdc.read_text() + "- enforced-by: no-such-check\n")


@pytest.fixture
def _add_check_with_missing_source(rules_sandbox: Path) -> None:
    (rules_sandbox / "lint" / "rules" / "no-linked-placeholder.yml").write_text(
        "id: no-linked-placeholder\nlanguage: Python\n"
        "metadata:\n  source: rules/missing.mdc\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )


@pytest.fixture
def exception_file(tmp_path: Path):
    def write(header: str) -> Path:
        path = tmp_path / "module.py"
        path.write_text(
            f"{header}# ast-grep-ignore: no-manual-init-boilerplate\n"
            "class Foo:\n    def __init__(self, name):\n        self.name = name\n"
        )
        return path

    return write


@pytest.fixture
def leaking_rule(tmp_path: Path) -> Path:
    path = tmp_path / "leaking-rule.yml"
    path.write_text(
        "id: no-direct-repository\n"
        "language: Python\n"
        "message: Do not instantiate InMemoryOrderRepository directly\n"
        "rule:\n"
        "  pattern: InMemoryOrderRepository()\n"
    )
    return path


@pytest.fixture
def rule_with_url_and_email(tmp_path: Path) -> Path:
    path = tmp_path / "contact-rule.yml"
    path.write_text(
        "note: |\n"
        "  Ask someone@internal-team.example.com or see https://wiki.internal.corp/page\n"
    )
    return path


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


@pytest.fixture
def add_hook_line(rules_sandbox: Path):
    def add(hook_id: str, mdc_name: str = "naming.mdc") -> None:
        mdc = rules_sandbox / "rules" / mdc_name
        mdc.write_text(
            mdc.read_text(encoding="utf-8") + f"- enforced-by-hook: {hook_id}\n",
            encoding="utf-8",
        )

    return add


@pytest.fixture
def _only_hook_in_checks_section(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "naming.mdc"
    prose = mdc.read_text(encoding="utf-8").split("## Checks")[0]
    mdc.write_text(
        prose + "## Checks\n- enforced-by-hook: gitleaks\n", encoding="utf-8"
    )


@pytest.fixture
def shell_exception_file(tmp_path: Path):
    def write(header: str) -> Path:
        path = tmp_path / "task.sh"
        path.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            f'{header}# ast-grep-ignore: no-eval\neval "$1"\n',
            encoding="utf-8",
        )
        return path

    return write


def coverage_issues(run_mstack, rules_sandbox: Path) -> tuple[int, list[tuple]]:
    completed = run_mstack("coverage", "--json", working_directory=rules_sandbox)
    issues = json.loads(completed.stdout)["issues"]
    return completed.returncode, [
        (issue["kind"], issue.get("check")) for issue in issues
    ]


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


def credit_rule(rules_sandbox: Path, credit: str) -> None:
    mdc = rules_sandbox / "rules" / "naming.mdc"
    mdc.write_text(mdc.read_text().replace("---\n", f"---\n{credit}", 1))
