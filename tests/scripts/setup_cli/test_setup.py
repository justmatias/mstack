import json
from pathlib import Path

import pytest


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): (
            f"-> {path.readlink()}" if path.is_symlink() else path.read_text()
        )
        for path in sorted(root.rglob("*"))
        if (path.is_file() or path.is_symlink()) and ".bak-" not in path.name
    }


def test_install_adds_hooks(
    setup_module, sandbox_root: Path, agent_components: list[str]
):
    setup_module.main(agent_components)

    claude = json.loads((sandbox_root / ".claude" / "settings.local.json").read_text())
    cursor = json.loads((sandbox_root / ".cursor" / "hooks.json").read_text())
    assert claude["hooks"]["PostToolUse"][0]["matcher"] == "Edit|Write"
    assert (
        cursor["hooks"]["postToolUse"][0]["command"]
        == "scripts/hooks/cursor_after_edit.sh"
    )
    assert not (sandbox_root / ".claude" / "skills").exists()


def test_install_twice_changes_nothing(
    setup_module, sandbox_root: Path, agent_components: list[str]
):
    setup_module.main(agent_components)
    first = snapshot(sandbox_root)

    setup_module.main(agent_components)

    assert snapshot(sandbox_root) == first


def test_install_merges_existing_settings(
    setup_module,
    sandbox_root: Path,
    existing_claude_settings: dict,
    agent_components: list[str],
):
    setup_module.main(agent_components)

    settings = json.loads(
        (sandbox_root / ".claude" / "settings.local.json").read_text()
    )
    assert settings["permissions"] == existing_claude_settings["permissions"]
    assert [entry["matcher"] for entry in settings["hooks"]["PostToolUse"]] == [
        "Bash",
        "Edit|Write",
    ]
    assert list((sandbox_root / ".claude").glob("settings.local.json.bak-*"))


@pytest.mark.usefixtures("existing_claude_settings")
def test_uninstall_restores_previous_state(
    setup_module,
    sandbox_root: Path,
    agent_components: list[str],
):
    before = snapshot(sandbox_root)
    setup_module.main(agent_components)

    setup_module.main([*agent_components, "--uninstall"])

    after = snapshot(sandbox_root)
    assert json.loads(after.pop(".claude/settings.local.json")) == json.loads(
        before.pop(".claude/settings.local.json")
    )
    assert after == before


def test_project_scope_writes_team_settings(setup_module, sandbox_root: Path):
    setup_module.main(["--with", "claude-hook", "--claude-settings", "project"])

    assert (sandbox_root / ".claude" / "settings.json").is_file()
    assert not (sandbox_root / ".claude" / "settings.local.json").exists()


def test_skills_are_no_longer_a_setup_component(setup_module):
    with pytest.raises(SystemExit):
        setup_module.main(["--with", "skills"])


def test_dry_run_writes_nothing(
    setup_module, sandbox_root: Path, agent_components: list[str]
):
    before = snapshot(sandbox_root)

    setup_module.main([*agent_components, "--dry-run"])

    assert snapshot(sandbox_root) == before
