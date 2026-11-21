import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mstack.cleanup import main

NOW = datetime(2026, 3, 15, tzinfo=UTC)
OLD = "20260101-000000"
NEWEST = "20260201-000000"


@pytest.fixture(autouse=True)
def isolated_folders(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-profile"))
    monkeypatch.setenv("MSTACK_PLATFORM", "linux")
    monkeypatch.setattr(
        "mstack.cleanup.run_quiet",
        lambda command: str(tmp_path / ("bin" if "--bin" in command else "uv-tools")),
    )


def backup(parent: Path, timestamp: str) -> Path:
    batch = parent / ".mstack-backups" / timestamp
    batch.mkdir(parents=True)
    (batch / "item").write_bytes(b"content")
    return batch


def test_cleanup_previews_reclaimable_size_when_apply_is_absent(tmp_path, capsys):
    old = backup(tmp_path / "uv-tools", OLD)
    backup(tmp_path / "uv-tools", NEWEST)

    assert main([], now=NOW) == 0

    assert old.is_dir()
    assert f"Would remove {old} (7 bytes)" in capsys.readouterr().out


def test_cleanup_keeps_latest_batch_when_all_backups_are_old(tmp_path):
    folder = tmp_path / ".agents" / "skills"
    old = backup(folder, OLD)
    newest = backup(folder, NEWEST)
    invalid = backup(folder, "20260231-000000")
    single = backup(tmp_path / "bin", OLD)

    assert main(["--apply"], now=NOW) == 0

    assert not old.exists()
    assert newest.is_dir()
    assert invalid.is_dir()
    assert single.is_dir()


def test_cleanup_keeps_batches_when_they_are_at_most_thirty_days_old(tmp_path):
    folder = tmp_path / "codex-profile" / "agents"
    old = backup(folder, OLD)
    cutoff = backup(folder, "20260213-000000")
    recent = backup(folder, "20260301-000000")

    assert main(["--apply"], now=NOW) == 0

    assert not old.exists()
    assert cutoff.is_dir()
    assert recent.is_dir()


def test_cleanup_scans_integration_backups_when_checkout_is_given(tmp_path):
    checkout = tmp_path / "checkout"
    skill_backups = checkout / "skills" / "toolkit"
    rule_backups = checkout / "policy"
    old_skill = backup(skill_backups, OLD)
    old_rule = backup(rule_backups, OLD)
    backup(skill_backups, NEWEST)
    backup(rule_backups, NEWEST)
    (checkout / ".mstack.toml").write_text('rules_dir = "policy"\n', encoding="utf-8")

    assert main(["--apply"], now=NOW) == 0
    assert old_skill.is_dir()
    assert old_rule.is_dir()

    assert main(["--apply", "--checkout", str(checkout)], now=NOW) == 0
    assert not old_skill.exists()
    assert not old_rule.exists()


@pytest.mark.skipif(
    sys.platform == "win32", reason="creating symlinks can require privileges"
)
def test_cleanup_preserves_link_targets_when_backup_folders_contain_symlinks(tmp_path):
    outside = tmp_path / "outside"
    external_batch = backup(outside, OLD)
    backup(outside, NEWEST)
    folder = tmp_path / "codex-profile"
    eligible = backup(folder, OLD)
    newest = backup(folder, NEWEST)
    (eligible / "link").symlink_to(external_batch, target_is_directory=True)
    (newest.parent / "20260102-000000").symlink_to(
        external_batch, target_is_directory=True
    )
    (folder / "agents").mkdir()
    (folder / "agents" / ".mstack-backups").symlink_to(
        external_batch.parent, target_is_directory=True
    )

    assert main(["--apply"], now=NOW) == 0

    assert not eligible.exists()
    assert (newest.parent / "20260102-000000").is_symlink()
    assert (external_batch / "item").is_file()


@pytest.mark.skipif(
    sys.platform == "win32", reason="creating symlinks can require privileges"
)
def test_cleanup_reports_an_invalid_checkout_when_a_symlink_loops(tmp_path, capsys):
    checkout = tmp_path / "checkout"
    checkout.symlink_to(checkout, target_is_directory=True)

    with pytest.raises(SystemExit) as error:
        main(["--checkout", str(checkout)], now=NOW)

    assert error.value.code == 2
    assert "invalid --checkout" in capsys.readouterr().err
