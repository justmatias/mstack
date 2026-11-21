import shlex

import pytest
import yaml

from mstack.cli import COMMANDS
from tests.conftest import REPOSITORY_ROOT, try_repo

HOOKS = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-hooks.yaml").read_text())


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
