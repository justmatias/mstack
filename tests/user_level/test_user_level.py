from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT
from tests.user_level.conftest import PREVIOUS_HOOKS_PATH, snapshot

PRINT_FILE = {"new.py": 'def do_work():\n    print("debug")\n'}
CLEAN_FILE = {"clean.py": "def do_work():\n    return 1\n"}
DATACLASS_FILE = {
    "model.py": "from dataclasses import dataclass\n\n\n@dataclass\nclass Foo:\n    name: str\n"
}


def global_hooks_path(run) -> str:
    return run("git", "config", "--global", "--get", "core.hooksPath").stdout.strip()


def test_install_twice_then_uninstall_restores_everything(
    setup_user, run, home_directory: Path, my_rules_home: Path
):
    before = snapshot(home_directory)

    setup_user("--replace-hooks-path")
    first = snapshot(home_directory)
    setup_user("--replace-hooks-path")
    second = snapshot(home_directory)
    assert global_hooks_path(run) == str(my_rules_home / "githooks")
    setup_user("--uninstall")

    assert second == first
    assert snapshot(home_directory) == before
    assert global_hooks_path(run) == PREVIOUS_HOOKS_PATH


def test_install_keeps_existing_hooks_path_without_flag(setup_user, run):
    completed = setup_user()

    assert global_hooks_path(run) == PREVIOUS_HOOKS_PATH
    assert "already /opt/previous/hooks" in completed.stderr


def test_install_never_overwrites_an_existing_set(setup_user, my_rules_home: Path):
    my_rules_home.mkdir(parents=True)
    (my_rules_home / "sgconfig.yml").write_text("ruleDirs: [mine]\n")

    setup_user("--with", "rules")

    assert (my_rules_home / "sgconfig.yml").read_text() == "ruleDirs: [mine]\n"


@pytest.mark.usefixtures("_install_personal_set")
def test_repository_without_hooks_rejects_staged_print(commit, repository_a: Path):
    completed = commit(repository_a, PRINT_FILE)

    assert completed.returncode != 0
    assert "my-no-print" in completed.stderr


@pytest.mark.usefixtures("_install_personal_set")
def test_old_print_in_unstaged_file_is_ignored(commit, repository_a: Path):
    (repository_a / "old.py").write_text('def legacy():\n    print("still old")\n')

    assert commit(repository_a, CLEAN_FILE).returncode == 0


@pytest.mark.usefixtures("_install_personal_set")
@pytest.mark.parametrize(
    ("files", "expected_success", "expected_message"),
    [
        (PRINT_FILE, False, "my-no-print"),
        ({"notes.txt": "hello\n"}, False, "text files are not allowed"),
        (CLEAN_FILE, True, ""),
    ],
    ids=["personal-fails", "repository-fails", "both-pass"],
)
def test_repository_with_pre_commit_runs_both(
    commit,
    repository_b: Path,
    files: dict,
    expected_success: bool,
    expected_message: str,
):
    completed = commit(repository_b, files)

    assert (completed.returncode == 0) is expected_success
    assert expected_message in completed.stdout + completed.stderr


@pytest.mark.usefixtures("_install_personal_set")
def test_local_commit_msg_hook_still_runs(commit, repository_c: Path):
    rejected = commit(repository_c, CLEAN_FILE, message="no prefix")
    accepted = commit(repository_c, CLEAN_FILE, message="OK with prefix")

    assert rejected.returncode != 0
    assert "must start with OK" in rejected.stderr
    assert accepted.returncode == 0


@pytest.mark.usefixtures("_install_personal_set")
def test_husky_repository_bypasses_personal_git_hook(
    commit, run, repository_d: Path, my_rules_home: Path
):
    completed = commit(repository_d, PRINT_FILE)
    agent_hook = run(
        str(my_rules_home / "bin" / "claude-post-edit"),
        input_text=f'{{"tool_input": {{"file_path": "{repository_d / "new.py"}"}}}}',
    )

    assert completed.returncode == 0
    assert agent_hook.returncode == 2
    assert "my-no-print" in agent_hook.stderr


@pytest.mark.usefixtures("_install_personal_set", "_ignore_repository_a_for_print")
def test_ignore_paths_silences_only_that_rule(commit, repository_a: Path):
    ignored = commit(repository_a, PRINT_FILE)
    reported = commit(repository_a, DATACLASS_FILE)

    assert ignored.returncode == 0
    assert reported.returncode != 0
    assert "my-prefer-pydantic" in reported.stderr


@pytest.mark.usefixtures("_install_personal_set")
def test_disable_variable_turns_everything_off(run, repository_a: Path):
    (repository_a / "new.py").write_text(PRINT_FILE["new.py"])
    run("git", "add", "new.py", cwd=repository_a)

    completed = run(
        "git",
        "commit",
        "-q",
        "-m",
        "skip",
        cwd=repository_a,
        extra={"MY_RULES_DISABLE": "1"},
    )

    assert completed.returncode == 0


@pytest.mark.usefixtures("_install_personal_set")
def test_claude_user_hook_reports_personal_and_repository_rules(
    run, my_rules_home: Path, claude_payload: str, repository_with_project_rules: Path
):
    completed = run(
        str(my_rules_home / "bin" / "claude-post-edit"),
        input_text=claude_payload,
        extra={"CLAUDE_PROJECT_DIR": str(repository_with_project_rules)},
    )

    assert completed.returncode == 2
    assert "my-prefer-pydantic" in completed.stderr
    assert "prefer-pydantic-over-dataclass" in completed.stderr


@pytest.mark.usefixtures("_install_personal_set", "_add_project_hook")
def test_claude_user_hook_skips_repository_set_when_project_hook_exists(
    run, my_rules_home: Path, claude_payload: str, repository_with_project_rules: Path
):
    completed = run(
        str(my_rules_home / "bin" / "claude-post-edit"),
        input_text=claude_payload,
        extra={"CLAUDE_PROJECT_DIR": str(repository_with_project_rules)},
    )

    assert completed.returncode == 2
    assert "my-prefer-pydantic" in completed.stderr
    assert "prefer-pydantic-over-dataclass" not in completed.stderr


@pytest.mark.usefixtures("_install_personal_set")
def test_cursor_user_hook_returns_additional_context(
    run, my_rules_home: Path, claude_payload: str
):
    completed = run(
        str(my_rules_home / "bin" / "cursor-after-edit"), input_text=claude_payload
    )

    assert completed.returncode == 0
    assert '"additional_context"' in completed.stdout
    assert "my-prefer-pydantic" in completed.stdout


@pytest.mark.usefixtures("_install_personal_set")
def test_personal_set_passes_its_own_tests_and_coverage(
    run, my_rules_home: Path, home_directory: Path
):
    tests = run(
        "ast-grep",
        "test",
        "-c",
        str(my_rules_home / "sgconfig.yml"),
        "--skip-snapshot-tests",
    )
    coverage = run(
        "python",
        str(REPOSITORY_ROOT / "scripts" / "check_rule_coverage.py"),
        "--rules-dir",
        str(home_directory / ".cursor" / "rules"),
        "--config",
        str(my_rules_home / "sgconfig.yml"),
        "--glob",
        "my-*.mdc",
        "--root",
        str(home_directory),
        cwd=home_directory,
    )

    assert tests.returncode == 0, tests.stdout + tests.stderr
    assert coverage.returncode == 0, coverage.stderr
