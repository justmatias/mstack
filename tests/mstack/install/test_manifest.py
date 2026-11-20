import json
import shutil

import pytest

from mstack.cli import main
from mstack.install import manifest


@pytest.mark.usefixtures("home")
def test_first_install_is_new(states):
    assert states() == {"skill:demo-skill": "new", "rule:demo": "new"}


@pytest.mark.usefixtures("home")
def test_setup_mstack_is_never_installed(states):
    assert "skill:setup-mstack" not in states("both")


@pytest.mark.usefixtures("home")
def test_cursor_gets_skills_but_no_rules(states):
    assert states("cursor") == {"skill:demo-skill": "new"}


def test_unrecorded_copy_equal_to_source_is_identical(install, states):
    install(record=False)

    assert states() == {"skill:demo-skill": "identical", "rule:demo": "identical"}


def test_unrecorded_identical_item_is_proposed_for_recording(install, checkout):
    install(record=False)

    rows = manifest.compute_status(checkout, "claude", manifest.Manifest())

    assert {row.action for row in rows} == {"record it"}


def test_unrecorded_copy_that_differs_is_unknown(install, states):
    skill_target, _ = install(record=False)
    (skill_target / "SKILL.md").write_text("# Mine\n")

    assert states()["skill:demo-skill"] == "unknown"


def test_second_run_after_install_is_identical(install, states):
    install()

    assert states() == {"skill:demo-skill": "identical", "rule:demo": "identical"}


def test_source_change_is_upstream_changed(install, checkout, states):
    install()
    (checkout / "skills" / "demo-skill" / "SKILL.md").write_text("# Newer\n")
    rule = checkout / "rules" / "demo.mdc"
    rule.write_text(rule.read_text().replace("Do the thing", "Do it better"))

    assert states() == {
        "skill:demo-skill": "upstream-changed",
        "rule:demo": "upstream-changed",
    }


def test_installed_change_is_locally_edited(install, states):
    skill_target, rule_target = install()
    (skill_target / "references" / "notes.md").write_text("My notes.\n")
    rule_target.write_text(rule_target.read_text() + "- My own line.\n")

    assert states() == {
        "skill:demo-skill": "locally-edited",
        "rule:demo": "locally-edited",
    }


def test_both_changed_is_conflict(install, checkout, states):
    skill_target, _ = install()
    (skill_target / "SKILL.md").write_text("# Mine\n")
    (checkout / "skills" / "demo-skill" / "SKILL.md").write_text("# Newer\n")

    assert states()["skill:demo-skill"] == "conflict"


def test_combined_item_recorded_after_install_is_identical(install, checkout, states):
    skill_target, _ = install(record=False)
    (skill_target / "SKILL.md").write_text("# Combined\n")
    manifest.main([
        "record",
        "skill",
        "demo-skill",
        str(skill_target),
        "--checkout",
        str(checkout),
    ])

    assert states()["skill:demo-skill"] == "identical"


def test_deleted_install_is_removed(install, states):
    skill_target, _ = install()
    shutil.rmtree(skill_target)

    assert states()["skill:demo-skill"] == "removed"


def test_item_gone_from_source_is_orphan(install, checkout, states):
    install()
    shutil.rmtree(checkout / "skills" / "demo-skill")

    assert states()["skill:demo-skill"] == "orphan"


def test_symlink_left_by_the_old_setup_is_reported(home, checkout, states):
    skills = home / ".claude" / "skills"
    skills.mkdir(parents=True)
    (skills / "demo-skill").symlink_to(checkout / "skills" / "demo-skill")

    assert states()["skill:demo-skill"] == "old-symlink"


def test_forget_drops_the_record(install, states):
    install()

    assert manifest.main(["forget", "skill", "demo-skill"]) == 0
    assert states()["skill:demo-skill"] == "identical"
    assert not manifest.load_manifest(manifest.manifest_path()).find(
        "skill", "demo-skill", manifest.expand("~/.claude/skills/demo-skill")
    )


def test_record_stores_hash_version_and_home_relative_target(install):
    install()

    data = json.loads(manifest.manifest_path().read_text())

    assert data["schema"] == 1
    skill = next(item for item in data["items"] if item["kind"] == "skill")
    assert skill["target"] == "~/.claude/skills/demo-skill"
    assert skill["hash"].startswith("sha256:")
    assert skill["installed_at"].endswith("Z")


@pytest.mark.usefixtures("home")
def test_manifest_lives_in_the_state_directory(tmp_path):
    assert manifest.manifest_path() == tmp_path / "state" / "mstack" / "manifest.json"


def test_record_of_missing_target_fails(home, checkout, caplog):
    missing = home / ".claude" / "skills" / "demo-skill"

    exit_code = manifest.main([
        "record",
        "skill",
        "demo-skill",
        str(missing),
        "--checkout",
        str(checkout),
    ])

    assert exit_code == 1
    assert "nothing is installed" in caplog.text


@pytest.mark.usefixtures("home")
def test_unknown_schema_fails_with_a_clear_message(checkout, caplog):
    path = manifest.manifest_path()
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema": 99, "items": []}))

    exit_code = manifest.main([
        "status",
        "--tool",
        "claude",
        "--checkout",
        str(checkout),
    ])

    assert exit_code == 1
    assert "schema 99" in caplog.text


@pytest.mark.usefixtures("home")
def test_write_is_atomic_and_leaves_no_temporary_file():
    path = manifest.manifest_path()
    manifest.save_manifest(manifest.Manifest(), path)
    manifest.save_manifest(manifest.Manifest(), path)

    assert [file.name for file in path.parent.iterdir()] == ["manifest.json"]


@pytest.mark.usefixtures("home")
def test_failed_write_keeps_the_previous_manifest(monkeypatch):
    path = manifest.manifest_path()
    manifest.save_manifest(manifest.Manifest(), path)
    previous = path.read_text()

    def fail(*_arguments):
        raise OSError("disk full")

    monkeypatch.setattr(manifest.os, "replace", fail)

    with pytest.raises(OSError):
        manifest.save_manifest(manifest.Manifest(), path)
    assert path.read_text() == previous
    assert [file.name for file in path.parent.iterdir()] == ["manifest.json"]


@pytest.mark.usefixtures("home")
def test_status_json_lists_every_item(checkout, capsys):
    exit_code = manifest.main([
        "status",
        "--tool",
        "both",
        "--json",
        "--checkout",
        str(checkout),
    ])

    rows = json.loads(capsys.readouterr().out)["items"]
    assert exit_code == 0
    assert {(row["kind"], row["name"], row["state"]) for row in rows} == {
        ("skill", "demo-skill", "new"),
        ("rule", "demo", "new"),
    }


def test_render_rule_command_prints_the_converted_rule(checkout, capsys):
    exit_code = main(["render-rule", str(checkout / "rules" / "demo.mdc")])

    assert exit_code == 0
    assert capsys.readouterr().out.startswith("Applies to files matching")
