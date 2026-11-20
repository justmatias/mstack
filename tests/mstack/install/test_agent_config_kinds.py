import json
import shutil
import subprocess
from pathlib import Path

import pytest

from mstack.install import manifest
from mstack.install.merge import merge_block_main, merge_settings_main

SERVER = {"command": "example-server", "env": {"EXAMPLE_TOKEN": "${EXAMPLE_TOKEN}"}}
SETTINGS = {"permissions": {"allow": ["Bash(mstack:*)"]}}


@pytest.fixture
def config_checkout(checkout: Path) -> Path:
    (checkout / "agents").mkdir()
    (checkout / "agents" / "README.md").write_text("# Agents\n")
    (checkout / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Reviews code\n---\n\nReview it.\n"
    )
    (checkout / "mcp").mkdir()
    (checkout / "mcp" / "example.json").write_text(json.dumps(SERVER))
    (checkout / "settings").mkdir()
    (checkout / "settings" / "claude.json").write_text(json.dumps(SETTINGS))
    (checkout / "instructions").mkdir()
    (checkout / "instructions" / "global.md").write_text("Shared text.\n")
    return checkout


@pytest.fixture
def install_config(config_checkout: Path, home: Path):
    """Install every new kind the way setup-mstack does, then record it."""

    def run() -> dict[str, Path]:
        claude = home / ".claude"
        targets = {
            "agent": claude / "agents" / "reviewer.md",
            "mcp": home / ".claude.json",
            "settings": claude / "settings.json",
            "instructions": claude / "CLAUDE.md",
        }
        targets["agent"].parent.mkdir(parents=True)
        shutil.copy(config_checkout / "agents" / "reviewer.md", targets["agent"])
        # Stands in for `claude mcp add-json --scope user`, which writes this file.
        merge_settings_main([
            str(config_checkout / "mcp" / "example.json"),
            str(targets["mcp"]),
            "--under",
            "mcpServers",
            "--under",
            "example",
            "--write",
        ])
        merge_settings_main([
            str(config_checkout / "settings" / "claude.json"),
            str(targets["settings"]),
            "--write",
        ])
        merge_block_main([
            str(config_checkout / "instructions" / "global.md"),
            str(targets["instructions"]),
            "--write",
        ])
        names = {"agent": "reviewer", "mcp": "example", "settings": "claude"}
        for kind, target in targets.items():
            manifest.main([
                "record",
                kind,
                names.get(kind, "global"),
                str(target),
                "--checkout",
                str(config_checkout),
            ])
        return targets

    return run


@pytest.fixture
def config_states(config_checkout: Path):
    def run(tool: manifest.Tool = "claude") -> dict[str, str]:
        loaded = manifest.load_manifest(manifest.manifest_path())
        return {
            f"{row.kind}:{row.name}:{row.target}": row.state
            for row in manifest.compute_status(config_checkout, tool, loaded)
            if row.kind not in {"skill", "rule"}
        }

    return run


@pytest.mark.usefixtures("home")
def test_clean_home_is_new(config_states):
    assert set(config_states().values()) == {"new"}


@pytest.mark.usefixtures("home")
def test_both_tools_merge_mcp_into_both_files(config_states):
    assert sorted(config_states("both")) == [
        "agent:reviewer:~/.claude/agents/reviewer.md",
        "instructions:global:~/.claude/CLAUDE.md",
        "mcp:example:~/.claude.json",
        "mcp:example:~/.cursor/mcp.json",
        "settings:claude:~/.claude/settings.json",
    ]


@pytest.mark.usefixtures("home")
def test_cursor_gets_agents_and_mcp_only(config_states):
    assert sorted(config_states("cursor")) == [
        "agent:reviewer:~/.cursor/agents/reviewer.md",
        "mcp:example:~/.cursor/mcp.json",
    ]


def test_second_run_is_identical(install_config, config_states):
    install_config()

    assert set(config_states().values()) == {"identical"}


def test_user_keys_and_text_do_not_change_the_state(install_config, config_states):
    targets = install_config()
    settings = json.loads(targets["settings"].read_text())
    settings["theme"] = "dark"
    settings["permissions"]["allow"].append("Bash(ls:*)")
    targets["settings"].write_text(json.dumps(settings))
    targets["instructions"].write_text(
        "# Mine\n\n" + targets["instructions"].read_text()
    )

    assert set(config_states().values()) == {"identical"}


def test_removing_every_key_mstack_wrote_is_removed(install_config, config_states):
    targets = install_config()
    targets["settings"].write_text(json.dumps({"permissions": {"allow": ["x"]}}))

    assert config_states()["settings:claude:~/.claude/settings.json"] == "removed"


def test_changing_a_value_mstack_wrote_is_locally_edited(install_config, config_states):
    targets = install_config()
    data = json.loads(targets["mcp"].read_text())
    data["mcpServers"]["example"]["command"] = "my-server"
    targets["mcp"].write_text(json.dumps(data))

    assert config_states()["mcp:example:~/.claude.json"] == "locally-edited"


def test_source_change_is_upstream_changed(
    install_config, config_checkout, config_states
):
    install_config()
    (config_checkout / "instructions" / "global.md").write_text("Newer text.\n")

    assert config_states()["instructions:global:~/.claude/CLAUDE.md"] == (
        "upstream-changed"
    )


def test_settings_record_stores_the_keys_written(install_config):
    install_config()

    data = json.loads(manifest.manifest_path().read_text())

    keys = {item["kind"]: item["keys"] for item in data["items"]}
    assert keys["settings"] == ["permissions.allow"]
    assert keys["mcp"] == [
        "mcpServers.example.command",
        "mcpServers.example.env.EXAMPLE_TOKEN",
    ]
    assert keys["agent"] is None


def test_removed_mcp_server_is_orphan(install_config, config_checkout, config_states):
    install_config()
    (config_checkout / "mcp" / "example.json").unlink()

    assert config_states()["mcp:example:~/.claude.json"] == "orphan"


def test_cli_lists_the_new_commands(repository_root: Path):
    completed = subprocess.run(
        ["uv", "run", "mstack", "--help"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )

    for command in ("merge-settings", "merge-block", "config-check"):
        assert command in completed.stdout
