import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.mstack.conftest import init_git_repository

USER_PRE_COMMIT = (
    "# my hooks\n"
    "repos:\n"
    "  - repo: https://github.com/pre-commit/pre-commit-hooks\n"
    "    rev: v6.0.0\n"
    "    hooks:\n"
    "      - id: check-yaml\n"
    "\n"
    "default_stages: [pre-commit]\n"
)


@pytest.fixture
def empty_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "work"
    repository.mkdir()
    return init_git_repository(repository)


@pytest.fixture
def run_init(empty_repository: Path):
    def run(*arguments: str, answer: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "mstack", "init", *arguments],
            cwd=empty_repository,
            input=answer,
            capture_output=True,
            text=True,
            check=False,
        )

    return run


def tree(repository: Path) -> dict[str, str]:
    return {
        path.relative_to(repository).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(repository.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(repository).parts
    }


def test_default_init_creates_the_layout_and_lint_passes(run_init, empty_repository):
    completed = run_init("--yes")

    assert completed.returncode == 0, completed.stderr
    assert sorted(tree(empty_repository)) == [
        ".cursor/rules/.gitkeep",
        ".mstack.toml",
        "lint-rules/rule-tests/.gitkeep",
        "lint-rules/rules/.gitkeep",
        "lint-rules/sgconfig.yml",
    ]
    assert "lint: scan OK" in completed.stderr


def test_custom_folders_are_written_to_the_config(run_init, empty_repository):
    run_init("--yes", "--rules-dir", "docs/rules", "--checks-dir", "checks")

    config = (empty_repository / ".mstack.toml").read_text(encoding="utf-8")
    assert 'rules_dir = "docs/rules"' in config
    assert 'sgconfig = "checks/sgconfig.yml"' in config
    assert (empty_repository / "checks" / "sgconfig.yml").is_file()


def test_second_run_changes_nothing(run_init, empty_repository):
    run_init("--yes", "--pre-commit", "--ci", "github", "--makefile")
    before = tree(empty_repository)

    completed = run_init("--yes", "--pre-commit", "--ci", "github", "--makefile")

    assert tree(empty_repository) == before
    assert "nothing to write" in completed.stderr


def test_existing_pre_commit_config_gets_the_hooks_appended(run_init, empty_repository):
    (empty_repository / ".pre-commit-config.yaml").write_text(USER_PRE_COMMIT)

    run_init("--yes", "--pre-commit")

    text = (empty_repository / ".pre-commit-config.yaml").read_text()
    config = yaml.safe_load(text)
    assert [repo["repo"] for repo in config["repos"]] == [
        "https://github.com/pre-commit/pre-commit-hooks",
        "https://github.com/justmatias/mstack",
    ]
    assert config["repos"][1]["rev"].startswith("v")
    assert config["default_stages"] == ["pre-commit"]
    assert text.startswith(USER_PRE_COMMIT.split("\n\n", maxsplit=1)[0])


def test_missing_pre_commit_config_is_created(run_init, empty_repository):
    run_init("--yes", "--pre-commit")

    config = yaml.safe_load((empty_repository / ".pre-commit-config.yaml").read_text())
    assert config["repos"][0]["hooks"][0]["id"] == "mstack-lint"


def test_existing_makefile_target_is_skipped(run_init, empty_repository):
    (empty_repository / "Makefile").write_text("lint-rules:\n\techo mine\n")

    run_init("--yes", "--makefile")

    makefile = (empty_repository / "Makefile").read_text()
    assert makefile.startswith("lint-rules:\n\techo mine\n")
    assert makefile.count("lint-rules:") == 1
    assert "lint-rules-changed:\n\tmstack lint --changed" in makefile


def test_workflow_uses_the_action_at_this_version(run_init, empty_repository):
    run_init("--yes", "--ci", "github")

    workflow = yaml.safe_load(
        (empty_repository / ".github" / "workflows" / "mstack.yml").read_text()
    )
    steps = workflow["jobs"]["lint"]["steps"]
    assert steps[0]["with"]["fetch-depth"] == 0
    assert steps[1]["uses"].startswith("justmatias/mstack@v")


def test_dry_run_writes_nothing(run_init, empty_repository):
    completed = run_init("--dry-run", "--pre-commit", "--makefile")

    assert completed.returncode == 0
    assert tree(empty_repository) == {}
    assert "create           .mstack.toml" in completed.stderr


def test_nothing_is_written_without_confirmation(run_init, empty_repository):
    completed = run_init(answer="n\n")

    assert completed.returncode == 1
    assert tree(empty_repository) == {}


def test_confirmation_writes_the_plan(run_init, empty_repository):
    completed = run_init(answer="y\n")

    assert completed.returncode == 0, completed.stderr
    assert (empty_repository / ".mstack.toml").is_file()


def test_existing_layout_is_left_as_it_is(run_init, empty_repository):
    (empty_repository / ".mstack.toml").write_text('rules_dir = "rules"\n')

    completed = run_init("--yes")

    assert (empty_repository / ".mstack.toml").read_text() == 'rules_dir = "rules"\n'
    assert not (empty_repository / "lint-rules").exists()
    assert "already exists" in completed.stderr
