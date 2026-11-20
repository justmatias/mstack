import json
import logging
from pathlib import Path

import pytest

from mstack.config import ConfigError, resolve_config


def test_defaults_without_file(git_repository: Path):
    config = resolve_config(start=git_repository)

    assert config.file is None
    assert config.root == git_repository
    assert config.values.rules_dir == git_repository / ".cursor/rules"
    assert config.values.sgconfig == git_repository / "lint-rules/sgconfig.yml"
    assert set(config.sources.values()) == {"default"}


def test_mstack_toml_only(git_repository: Path, write_config):
    write_config('rules_dir = "rules"\n[scan]\nexclude = ["generated/**"]\n')

    config = resolve_config(start=git_repository)

    assert config.values.rules_dir == git_repository / "rules"
    assert config.values.scan.exclude == ["generated/**"]
    assert config.sources["rules_dir"] == "file"
    assert config.sources["scan.exclude"] == "file"
    assert config.sources["scan.extensions"] == "default"


def test_pyproject_table_only(git_repository: Path, write_config):
    write_config('[tool.mstack]\nrules_dir = "rules"\n', name="pyproject.toml")

    config = resolve_config(start=git_repository)

    assert config.file == git_repository / "pyproject.toml"
    assert config.values.rules_dir == git_repository / "rules"


def test_pyproject_without_table_is_ignored(git_repository: Path, write_config):
    write_config('[project]\nname = "sample"\n', name="pyproject.toml")

    assert resolve_config(start=git_repository).file is None


def test_mstack_toml_wins_over_pyproject_with_warning(
    git_repository: Path, write_config, caplog
):
    write_config('rules_dir = "from-mstack-toml"\n')
    write_config('[tool.mstack]\nrules_dir = "from-pyproject"\n', "pyproject.toml")

    with caplog.at_level(logging.WARNING):
        config = resolve_config(start=git_repository)

    assert config.values.rules_dir == git_repository / "from-mstack-toml"
    assert "using .mstack.toml" in caplog.text


@pytest.mark.parametrize(
    "content",
    ['rule_dir = "rules"\n', '[scan]\nexcludes = ["generated/**"]\n'],
    ids=["top-level", "nested"],
)
def test_unknown_key_fails(git_repository: Path, write_config, content: str):
    write_config(content)

    with pytest.raises(ConfigError, match="Extra inputs are not permitted"):
        resolve_config(start=git_repository)


def test_flag_overrides_file(git_repository: Path, write_config, monkeypatch):
    write_config('rules_dir = "rules"\n')
    monkeypatch.chdir(git_repository)

    config = resolve_config({"rules_dir": Path("other-rules"), "sgconfig": None})

    assert config.values.rules_dir == git_repository / "other-rules"
    assert config.sources["rules_dir"] == "flag"
    assert config.sources["sgconfig"] == "default"


def test_discovery_from_subfolder(git_repository: Path, write_config):
    write_config('rules_dir = "rules"\n')
    subfolder = git_repository / "package" / "module"
    subfolder.mkdir(parents=True)

    config = resolve_config(start=subfolder)

    assert config.file == git_repository / ".mstack.toml"
    assert config.values.rules_dir == git_repository / "rules"


def test_discovery_stops_at_git_root(git_repository: Path):
    (git_repository.parent / ".mstack.toml").write_text('rules_dir = "outside"\n')

    config = resolve_config(start=git_repository)

    assert config.file is None
    assert config.values.rules_dir == git_repository / ".cursor/rules"


def test_config_command_reports_sources(run_mstack, write_config, git_repository):
    write_config('rules_dir = "rules"\n')

    completed = run_mstack(
        "config",
        "--sgconfig",
        "checks/sgconfig.yml",
        "--json",
        working_directory=git_repository,
    )

    settings = json.loads(completed.stdout)["settings"]
    assert completed.returncode == 0, completed.stderr
    assert settings["rules_dir"] == {"value": "rules", "source": "file"}
    assert settings["sgconfig"] == {"value": "checks/sgconfig.yml", "source": "flag"}
    assert settings["importlinter"] == {"value": ".importlinter", "source": "default"}


def test_invalid_config_exits_with_message(run_mstack, write_config, git_repository):
    write_config('rules_dir = ["not", "a", "path"]\n')

    completed = run_mstack("coverage", working_directory=git_repository)

    assert completed.returncode == 2
    assert ".mstack.toml" in completed.stderr
