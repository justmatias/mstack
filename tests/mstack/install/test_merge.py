import json
from pathlib import Path

import pytest

from mstack.install.merge import (
    BLOCK_BEGIN,
    BLOCK_END,
    apply_block,
    deep_merge,
    extract_block,
    leaf_keys,
    merge_block_main,
    merge_settings_main,
    project,
)

USER_SETTINGS = {
    "permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(rm:*)"]},
    "theme": "dark",
    "statusLine": {"type": "command", "command": "old"},
}
FRAGMENT = {
    "permissions": {"allow": ["Bash(ls:*)", "Bash(mstack:*)"]},
    "statusLine": {"command": "new"},
    "env": {"EXAMPLE": "1"},
}


def test_arrays_are_unions_in_order():
    merged, _ = deep_merge(USER_SETTINGS, FRAGMENT)

    assert merged["permissions"]["allow"] == ["Bash(ls:*)", "Bash(mstack:*)"]


def test_user_keys_are_preserved():
    merged, _ = deep_merge(USER_SETTINGS, FRAGMENT)

    assert merged["theme"] == "dark"
    assert merged["permissions"]["deny"] == ["Bash(rm:*)"]
    assert merged["statusLine"]["type"] == "command"


def test_nested_scalars_from_the_fragment_win_and_every_change_is_listed():
    merged, changes = deep_merge(USER_SETTINGS, FRAGMENT)

    assert merged["statusLine"]["command"] == "new"
    assert {(change.key, change.action) for change in changes} == {
        ("permissions.allow", "extend"),
        ("statusLine.command", "change"),
        ("env", "add"),
    }


def test_merging_twice_changes_nothing_the_second_time():
    once, _ = deep_merge(USER_SETTINGS, FRAGMENT)
    twice, changes = deep_merge(once, FRAGMENT)

    assert twice == once
    assert not changes


def test_inputs_are_not_modified():
    before = json.dumps(USER_SETTINGS)

    deep_merge(USER_SETTINGS, FRAGMENT)

    assert json.dumps(USER_SETTINGS) == before


def test_projection_equals_the_fragment_once_merged():
    merged, _ = deep_merge(USER_SETTINGS, FRAGMENT)

    assert project(merged, FRAGMENT) == FRAGMENT
    assert project({}, FRAGMENT) is None


def test_leaf_keys_name_what_mstack_writes():
    assert leaf_keys(FRAGMENT) == [
        "permissions.allow",
        "statusLine.command",
        "env.EXAMPLE",
    ]


@pytest.fixture
def settings_files(tmp_path: Path) -> tuple[Path, Path]:
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps(FRAGMENT))
    target = tmp_path / "settings.json"
    target.write_text(json.dumps(USER_SETTINGS))
    return fragment, target


def test_dry_run_writes_nothing(settings_files, capsys):
    fragment, target = settings_files
    before = target.read_text()

    exit_code = merge_settings_main([str(fragment), str(target), "--dry-run"])

    assert exit_code == 0
    assert target.read_text() == before
    assert len(json.loads(capsys.readouterr().out)["changes"]) == 3


def test_write_merges_and_a_second_write_reports_no_change(settings_files, capsys):
    fragment, target = settings_files

    merge_settings_main([str(fragment), str(target), "--write"])
    capsys.readouterr()
    merge_settings_main([str(fragment), str(target), "--write"])

    assert not json.loads(capsys.readouterr().out)["changes"]
    assert json.loads(target.read_text())["theme"] == "dark"


def test_under_nests_the_fragment(tmp_path: Path):
    fragment = tmp_path / "server.json"
    fragment.write_text(json.dumps({"command": "example-server"}))
    target = tmp_path / "mcp.json"
    nesting = ["--under", "mcpServers", "--under", "example"]

    merge_settings_main([str(fragment), str(target), *nesting, "--write"])

    assert json.loads(target.read_text()) == {
        "mcpServers": {"example": {"command": "example-server"}}
    }


def test_invalid_target_fails(settings_files, caplog):
    fragment, target = settings_files
    target.write_text("[1, 2]")

    assert merge_settings_main([str(fragment), str(target), "--dry-run"]) == 1
    assert "not a JSON object" in caplog.text


def test_block_is_appended_when_missing():
    updated = apply_block("# Mine\n", "Shared text.\n")

    assert updated == f"# Mine\n\n{BLOCK_BEGIN}\nShared text.\n{BLOCK_END}\n"


def test_block_is_replaced_and_outside_text_kept():
    text = f"Before.\n\n{BLOCK_BEGIN}\nOld.\n{BLOCK_END}\n\nAfter.\n"

    updated = apply_block(text, "New.\n")

    assert updated == f"Before.\n\n{BLOCK_BEGIN}\nNew.\n{BLOCK_END}\n\nAfter.\n"
    assert extract_block(updated) == "New.\n"


def test_block_in_an_empty_file():
    assert apply_block("", "Text.") == f"{BLOCK_BEGIN}\nText.\n{BLOCK_END}\n"


def test_merge_block_dry_run_writes_nothing_and_rerun_is_unchanged(
    tmp_path: Path, capsys
):
    block = tmp_path / "global.md"
    block.write_text("Shared text.\n")
    target = tmp_path / "CLAUDE.md"
    target.write_text("# Mine\n")

    merge_block_main([str(block), str(target), "--dry-run"])
    assert target.read_text() == "# Mine\n"
    merge_block_main([str(block), str(target), "--write"])
    capsys.readouterr()
    merge_block_main([str(block), str(target), "--write"])

    assert json.loads(capsys.readouterr().out)["changed"] is False
    assert target.read_text().startswith("# Mine\n")
