import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.conftest import REPOSITORY_ROOT, run_command


@pytest.fixture
def run_mstack():
    def run(command: str, *arguments: str, working_directory: Path = REPOSITORY_ROOT):
        return run_command(
            [sys.executable, "-m", "mstack", command, *arguments], working_directory
        )

    return run


@pytest.fixture
def git_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    (repository / ".git").mkdir(parents=True)
    return repository


@pytest.fixture
def write_config(git_repository: Path):
    def write(content: str, name: str = ".mstack.toml") -> Path:
        path = git_repository / name
        path.write_text(content, encoding="utf-8")
        return path

    return write


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def init_git_repository(repository: Path) -> Path:
    git(repository, "init", "--quiet", "--initial-branch=main")
    git(repository, "config", "user.email", "tests@example.invalid")
    git(repository, "config", "user.name", "Tests")
    git(repository, "config", "commit.gpgsign", "false")
    git(repository, "add", "--all")
    git(repository, "commit", "--quiet", "--allow-empty", "-m", "initial")
    return repository


@pytest.fixture
def commit():
    def run(repository: Path, message: str = "change") -> None:
        git(repository, "add", "--all")
        git(repository, "commit", "--quiet", "-m", message)

    return run


@pytest.fixture
def feature_repository(tmp_path: Path) -> Path:
    """A real git repo with a.py, b.py and notes.txt on main, checked out on feature."""
    repository = tmp_path / "feature"
    repository.mkdir()
    for name in ("a.py", "b.py", "notes.txt"):
        (repository / name).write_text("x = 1\n", encoding="utf-8")
    init_git_repository(repository)
    git(repository, "checkout", "--quiet", "-b", "feature")
    return repository


@pytest.fixture
def lint_sandbox(tmp_path: Path) -> Path:
    """A committed git repo with this repo's rules, checks, fixtures and config."""
    sandbox = tmp_path / "sandbox"
    ignore = shutil.ignore_patterns("__pycache__")
    for folder in ("rules", "lint", "fixtures"):
        shutil.copytree(REPOSITORY_ROOT / folder, sandbox / folder, ignore=ignore)
    for name in (".mstack.toml", ".importlinter", ".pre-commit-config.yaml"):
        if (REPOSITORY_ROOT / name).is_file():
            shutil.copy(REPOSITORY_ROOT / name, sandbox / name)
    return init_git_repository(sandbox)


@pytest.fixture
def expected_rendering():
    """The conversion setup-mstack step 3 describes, written independently."""

    def credit(frontmatter: str) -> str:
        metadata = (yaml.safe_load(frontmatter) or {}).get("metadata") or {}
        if "adapted-from" not in metadata:
            return ""
        return (
            f"\n\nAdapted from {metadata['adapted-from']} "
            f"License: {metadata['upstream-license']}."
        )

    def expected(mdc_text: str) -> str:
        _, frontmatter, body = mdc_text.split("---\n", 2)
        globs_line = next(
            (line for line in frontmatter.splitlines() if line.startswith("globs:")),
            None,
        )
        body = body.split("## Checks")[0].strip() + credit(frontmatter)
        if globs_line is None:
            return f"{body}\n"
        globs = globs_line.removeprefix("globs:").strip().strip('"')
        return f"Applies to files matching `{globs}`.\n\n{body}\n"

    return expected


@pytest.fixture
def run_lint(run_mstack, lint_sandbox: Path):
    def run(*arguments: str) -> tuple[int, dict]:
        completed = run_mstack(
            "lint", "--json", *arguments, working_directory=lint_sandbox
        )
        return completed.returncode, json.loads(completed.stdout)

    return run


@pytest.fixture
def import_contract(lint_sandbox: Path):
    """A package whose core imports its adapters, and a contract forbidding it."""

    def write(core_imports_adapters: bool) -> None:
        package = lint_sandbox / "app"
        (package / "core").mkdir(parents=True)
        (package / "adapters").mkdir()
        for init in (package, package / "core", package / "adapters"):
            (init / "__init__.py").write_text("", encoding="utf-8")
        source = "from app.adapters import store\n" if core_imports_adapters else ""
        (package / "core" / "logic.py").write_text(source, encoding="utf-8")
        (package / "adapters" / "store.py").write_text("", encoding="utf-8")
        (lint_sandbox / ".importlinter").write_text(
            "[importlinter]\nroot_package = app\n\n"
            "[importlinter:contract:core-is-pure]\nname = core-is-pure\n"
            "type = forbidden\nsource_modules = app.core\n"
            "forbidden_modules = app.adapters\n",
            encoding="utf-8",
        )

    return write


@pytest.fixture
def pack_consumer(tmp_path: Path):
    git(tmp_path, "init", "--quiet")
    shutil.copy(
        REPOSITORY_ROOT / "fixtures" / "invalid" / "error-handling" / "bare_except.py",
        tmp_path / "target.py",
    )

    def configure(extra: str = "") -> None:
        (tmp_path / ".mstack.toml").write_text(
            'packs = ["python-core"]\n' + extra, encoding="utf-8"
        )

    configure()
    return configure


@pytest.fixture
def run_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setenv("TEMP", str(tmp_path))
    monkeypatch.setenv("TMP", str(tmp_path))

    def run(repository: Path, event: str, **payload: object):
        return subprocess.run(
            [sys.executable, "-m", "mstack", "hook", event],
            cwd=tmp_path,
            input=json.dumps({"cwd": str(repository), **payload}),
            capture_output=True,
            text=True,
            check=False,
        )

    return run
