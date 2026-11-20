import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

from mstack.cli import COMMANDS
from tests.conftest import REPOSITORY_ROOT

HOOKS = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-hooks.yaml").read_text())
BARE_EXCEPT_RULE = REPOSITORY_ROOT / "lint" / "rules" / "no-bare-except.yml"


@pytest.mark.parametrize("hook", HOOKS, ids=lambda hook: hook["id"])
def test_every_entry_is_an_mstack_command(hook: dict):
    program, command, *_ = shlex.split(hook["entry"])

    assert (program, command in COMMANDS) == ("mstack", True)


@pytest.mark.parametrize("hook", HOOKS, ids=lambda hook: hook["id"])
def test_every_hook_installs_mstack_as_python(hook: dict):
    assert hook["language"] == "python"


def test_hook_ids_are_unique():
    ids = [hook["id"] for hook in HOOKS]

    assert len(ids) == len(set(ids))


@pytest.fixture
def repository_with_a_rule(tmp_path: Path) -> Path:
    """A repo with the default layout: one prose rule and its ast-grep check."""
    repository = tmp_path / "target"
    (repository / "lint-rules" / "rules").mkdir(parents=True)
    (repository / ".cursor" / "rules").mkdir(parents=True)
    (repository / "lint-rules" / "sgconfig.yml").write_text("ruleDirs:\n  - rules\n")
    (repository / "lint-rules" / "rules" / BARE_EXCEPT_RULE.name).write_text(
        BARE_EXCEPT_RULE.read_text().replace(
            "rules/error-handling.mdc", ".cursor/rules/error-handling.mdc"
        )
    )
    (repository / ".cursor" / "rules" / "error-handling.mdc").write_text(
        "# Error handling\n\n- Name the exception you expect.\n\n"
        "## Checks\n- enforced-by: no-bare-except\n"
    )
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
    return repository


def try_repo(
    repository: Path, source: str, *hook_id: str
) -> subprocess.CompletedProcess:
    (repository / "module.py").write_text(source)
    subprocess.run(["git", "add", "--all"], cwd=repository, check=True)
    return subprocess.run(
        ["pre-commit", "try-repo", str(REPOSITORY_ROOT), *hook_id, "--all-files"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.slow
def test_try_repo_fails_on_a_bad_file_and_passes_once_fixed(repository_with_a_rule):
    bad = "try:\n    run()\nexcept:\n    raise\n"
    fixed = "try:\n    run()\nexcept ValueError:\n    raise\n"

    assert try_repo(repository_with_a_rule, bad, "mstack-lint").returncode == 1
    assert try_repo(repository_with_a_rule, fixed, "mstack-lint").returncode == 0


@pytest.mark.slow
def test_try_repo_runs_every_hook_on_a_clean_repository(repository_with_a_rule):
    completed = try_repo(repository_with_a_rule, "VALUE = 1\n")

    assert completed.returncode == 0, completed.stdout
