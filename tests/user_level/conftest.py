import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT

VIRTUAL_ENVIRONMENT_BIN = Path(sys.executable).parent
PREVIOUS_HOOKS_PATH = "/opt/previous/hooks"


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): (
            f"-> {os.readlink(path)}" if path.is_symlink() else path.read_text()
        )
        for path in sorted(root.rglob("*"))
        if (path.is_file() or path.is_symlink())
        and ".bak-" not in path.name
        and ".gitconfig" not in path.name
    }


@pytest.fixture
def home_directory(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}})
    )
    return home


@pytest.fixture
def environment(home_directory: Path) -> dict[str, str]:
    global_config = home_directory / ".gitconfig"
    global_config.write_text(
        f"[user]\n\tname = Test\n\temail = test@example.invalid\n[init]\n\tdefaultBranch = main\n"
        f"[core]\n\thooksPath = {PREVIOUS_HOOKS_PATH}\n"
    )
    return {
        **{
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("GIT_", "MY_RULES", "XDG_"))
        },
        "HOME": str(home_directory),
        "GIT_CONFIG_GLOBAL": str(global_config),
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": f"{VIRTUAL_ENVIRONMENT_BIN}{os.pathsep}{os.environ['PATH']}",
        "AST_GREP": str(VIRTUAL_ENVIRONMENT_BIN / "ast-grep"),
        "PRE_COMMIT_HOME": str(home_directory / ".cache" / "pre-commit"),
    }


@pytest.fixture
def run(environment: dict[str, str]):
    def execute(
        *command: str,
        cwd: Path | None = None,
        input_text: str | None = None,
        extra: dict | None = None,
    ):
        return subprocess.run(
            command,
            cwd=cwd,
            env={**environment, **(extra or {})},
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    return execute


@pytest.fixture
def setup_user(run):
    def install(*arguments: str):
        completed = run(
            sys.executable,
            str(REPOSITORY_ROOT / "scripts" / "setup.py"),
            "user",
            "--yes",
            *arguments,
        )
        assert completed.returncode == 0, completed.stderr
        return completed

    return install


@pytest.fixture
def _install_personal_set(setup_user) -> None:
    setup_user("--replace-hooks-path")


@pytest.fixture
def my_rules_home(home_directory: Path) -> Path:
    return home_directory / ".config" / "my-rules"


@pytest.fixture
def make_repository(tmp_path: Path, run):
    def create(name: str) -> Path:
        repository = tmp_path / "work" / name
        repository.mkdir(parents=True)
        run("git", "init", "-q", cwd=repository)
        (repository / "old.py").write_text('def legacy():\n    print("old")\n')
        run("git", "add", "old.py", cwd=repository)
        run(
            "git",
            "commit",
            "-q",
            "-m",
            "initial",
            cwd=repository,
            extra={"MY_RULES_DISABLE": "1"},
        )
        return repository

    return create


@pytest.fixture
def commit(run):
    def stage_and_commit(
        repository: Path, files: dict[str, str], message: str = "change"
    ):
        for name, content in files.items():
            (repository / name).write_text(content)
            run("git", "add", name, cwd=repository)
        return run("git", "commit", "-q", "-m", message, cwd=repository)

    return stage_and_commit


@pytest.fixture
def repository_a(make_repository) -> Path:
    return make_repository("repository-a")


@pytest.fixture
def repository_b(make_repository, run) -> Path:
    repository = make_repository("repository-b")
    (repository / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n"
        "      - id: no-text-files\n        name: no text files\n"
        "        language: fail\n        entry: text files are not allowed\n"
        "        files: \\.txt$\n"
    )
    run("git", "add", ".pre-commit-config.yaml", cwd=repository)
    run(
        "git",
        "commit",
        "-q",
        "-m",
        "add pre-commit config",
        cwd=repository,
        extra={"MY_RULES_DISABLE": "1"},
    )
    return repository


@pytest.fixture
def repository_c(make_repository) -> Path:
    repository = make_repository("repository-c")
    hook = repository / ".git" / "hooks" / "commit-msg"
    hook.write_text(
        "#!/usr/bin/env bash\n"
        'grep -q "^OK" "$1" || { echo "commit-msg: must start with OK" >&2; exit 1; }\n'
    )
    hook.chmod(0o755)
    return repository


@pytest.fixture
def repository_d(make_repository, run) -> Path:
    repository = make_repository("repository-d")
    husky = repository / ".husky"
    husky.mkdir()
    (husky / "pre-commit").write_text("#!/usr/bin/env bash\nexit 0\n")
    (husky / "pre-commit").chmod(0o755)
    run("git", "config", "core.hooksPath", ".husky", cwd=repository)
    return repository


@pytest.fixture
def _ignore_repository_a_for_print(my_rules_home: Path, repository_a: Path) -> None:
    with (my_rules_home / "ignore-paths.txt").open("a") as ignore_file:
        ignore_file.write(f"{repository_a}/** my-no-print\n")


@pytest.fixture
def repository_with_project_rules(make_repository) -> Path:
    repository = make_repository("repository-with-rules")
    shutil.copytree(REPOSITORY_ROOT / "lint-rules", repository / "lint-rules")
    return repository


@pytest.fixture
def _add_project_hook(repository_with_project_rules: Path) -> None:
    settings = repository_with_project_rules / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps({
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {
                                "type": "command",
                                "command": (
                                    '"$CLAUDE_PROJECT_DIR"'
                                    "/scripts/hooks/claude_post_edit.sh"
                                ),
                            }
                        ],
                    }
                ]
            }
        })
    )


@pytest.fixture
def dataclass_file(repository_with_project_rules: Path) -> Path:
    path = repository_with_project_rules / "model.py"
    path.write_text(
        "from dataclasses import dataclass\n\n\n@dataclass\nclass Foo:\n    name: str\n"
        "\n\ntry:\n    Foo(name='x')\nexcept:\n    raise\n"
    )
    return path


@pytest.fixture
def claude_payload(dataclass_file: Path) -> str:
    return json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": str(dataclass_file)},
    })
