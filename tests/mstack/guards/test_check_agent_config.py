import json
from pathlib import Path

import pytest

from mstack.guards.check_agent_config import collect_problems


@pytest.fixture
def config_root(tmp_path: Path) -> Path:
    for folder in ("agents", "mcp", "settings", "instructions"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "README.md").write_text("# Format\n")
    return tmp_path


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data))


def test_valid_folders_pass(config_root: Path):
    (config_root / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Reviews code\n---\nReview.\n"
    )
    write_json(
        config_root / "mcp" / "example.json",
        {"command": "example", "env": {"EXAMPLE_TOKEN": "${EXAMPLE_TOKEN}"}},
    )
    write_json(config_root / "settings" / "claude.json", {"env": {"PATH_X": "~/bin"}})
    (config_root / "instructions" / "global.md").write_text("Use ${HOME}/bin.\n")

    assert not collect_problems(config_root)


def test_agent_name_must_match_the_file(config_root: Path):
    (config_root / "agents" / "reviewer.md").write_text(
        "---\nname: other\ndescription: Reviews code\n---\n"
    )

    assert "must be 'reviewer'" in collect_problems(config_root)[0]


def test_agent_needs_a_description(config_root: Path):
    (config_root / "agents" / "reviewer.md").write_text("---\nname: reviewer\n---\n")

    assert "needs a description" in collect_problems(config_root)[0]


@pytest.mark.parametrize(
    "env",
    [
        {"EXAMPLE_TOKEN": "plain-literal-value"},
        {"HEADER": "Bearer abcdefgh12345678"},
        {"GITHUB": "ghp_" + "a" * 36},
    ],
    ids=["sensitive-key", "bearer", "token-pattern"],
)
def test_literal_secret_in_mcp_fails(config_root: Path, env: dict):
    write_json(config_root / "mcp" / "example.json", {"command": "x", "env": env})

    assert "literal secret" in collect_problems(config_root)[0]


def test_literal_secret_in_settings_fails(config_root: Path):
    write_json(config_root / "settings" / "claude.json", {"env": {"API_KEY": "abc"}})

    assert "literal secret" in collect_problems(config_root)[0]


def test_invalid_json_fails(config_root: Path):
    (config_root / "settings" / "claude.json").write_text("{not json")

    assert "invalid JSON" in collect_problems(config_root)[0]


def test_mcp_entry_needs_a_command_or_url(config_root: Path):
    write_json(config_root / "mcp" / "example.json", {"args": []})

    assert "'command' or a 'url'" in collect_problems(config_root)[0]


def test_machine_specific_path_fails(config_root: Path):
    write_json(
        config_root / "mcp" / "example.json", {"command": "/home/someone/bin/server"}
    )

    assert "machine-specific path" in collect_problems(config_root)[0]


def test_repository_folders_pass(run_mstack):
    completed = run_mstack("config-check")

    assert completed.returncode == 0, completed.stderr
