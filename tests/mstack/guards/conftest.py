import shutil
from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT


@pytest.fixture
def rules_sandbox(tmp_path: Path) -> Path:
    shutil.copytree(REPOSITORY_ROOT / "rules", tmp_path / "rules")
    shutil.copytree(REPOSITORY_ROOT / "lint", tmp_path / "lint")
    shutil.copy(REPOSITORY_ROOT / ".mstack.toml", tmp_path / ".mstack.toml")
    return tmp_path


@pytest.fixture
def _delete_enforced_by_line(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "error-handling.mdc"
    mdc.write_text(
        mdc.read_text().replace("- enforced-by: no-swallowed-exception\n", "")
    )


@pytest.fixture
def _delete_checks_section(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "naming.mdc"
    mdc.write_text(mdc.read_text().split("## Checks")[0])


@pytest.fixture
def _add_unknown_check(rules_sandbox: Path) -> None:
    mdc = rules_sandbox / "rules" / "logging.mdc"
    mdc.write_text(mdc.read_text() + "- enforced-by: no-such-check\n")


@pytest.fixture
def _point_rule_to_missing_source(rules_sandbox: Path) -> None:
    rule = rules_sandbox / "lint" / "rules" / "no-bare-except.yml"
    rule.write_text(rule.read_text().replace("error-handling.mdc", "missing.mdc"))


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
    shutil.copytree(REPOSITORY_ROOT / "skills", tmp_path / "skills")
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
def pre_commit_config(rules_sandbox: Path) -> Path:
    path = rules_sandbox / ".pre-commit-config.yaml"
    path.write_text(
        "repos:\n"
        "  - repo: https://github.com/gitleaks/gitleaks\n"
        "    rev: v8.30.0\n"
        "    hooks:\n"
        "      - id: gitleaks\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: check-something\n"
        "        name: check something\n"
        "        entry: true\n"
        "        language: system\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def add_hook_line(rules_sandbox: Path):
    def add(hook_id: str, mdc_name: str = "logging.mdc") -> None:
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
