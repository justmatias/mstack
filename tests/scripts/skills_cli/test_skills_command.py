# pylint: disable=too-many-arguments,too-many-positional-arguments
import json
import subprocess
from pathlib import Path

import pytest

from tests.scripts.skills_cli.conftest import SKILL_NAMES, snapshot, write_skill


def test_fresh_install_then_second_run_changes_nothing(
    install_everything, plan_skills, apply_skills, actions, home_directory: Path
):
    first = install_everything()

    assert set(actions(first).values()) == {"install"}
    second = plan_skills()
    assert actions(second) == dict.fromkeys(SKILL_NAMES, "unchanged")
    before = snapshot(home_directory)
    assert apply_skills({}) == 0
    assert snapshot(home_directory) == before


def test_setup_skill_is_never_installed(
    install_everything, claude_skills: Path, actions
):
    plan = install_everything()

    assert "setup-mstack" not in actions(plan)
    assert not (claude_skills / "setup-mstack").exists()


def test_installed_skills_are_copies(install_everything, claude_skills: Path):
    install_everything()

    for name in SKILL_NAMES:
        assert (claude_skills / name).is_dir()
        assert not (claude_skills / name).is_symlink()
    manifest = json.loads((claude_skills / ".mstack-manifest.json").read_text())
    assert set(manifest["skills"]) == set(SKILL_NAMES)
    assert {"version", "toolkit_path", "source_commit", "installed_at"} <= set(manifest)
    assert manifest["skills"]["sync-rules"]["files"] == [
        "SKILL.md",
        "references/principles.md",
    ]


def test_source_change_gives_update(
    install_everything,
    plan_skills,
    apply_skills,
    actions,
    toolkit_root: Path,
    claude_skills: Path,
):
    install_everything()
    (toolkit_root / "skills" / "sync-rules" / "references" / "new.md").write_text("x\n")

    assert actions(plan_skills())["sync-rules"] == "update"
    assert apply_skills({"sync-rules": "update"}) == 0
    assert (claude_skills / "sync-rules" / "references" / "new.md").is_file()
    assert actions(plan_skills())["sync-rules"] == "unchanged"


def test_local_edit_is_never_overwritten_without_a_decision(
    install_everything,
    plan_skills,
    apply_skills,
    actions,
    toolkit_root: Path,
    claude_skills: Path,
):
    install_everything()
    edited = claude_skills / "reflect-rules" / "SKILL.md"
    edited.write_text(edited.read_text() + "\nMy own note.\n")
    (toolkit_root / "skills" / "reflect-rules" / "extra.md").write_text("new\n")

    assert actions(plan_skills())["reflect-rules"] == "modified-locally"
    assert apply_skills({}) == 1
    assert apply_skills({"reflect-rules": "update"}) == 1
    assert "My own note." in edited.read_text()
    assert apply_skills({"reflect-rules": "keep-mine"}) == 0
    assert "My own note." in edited.read_text()
    assert actions(plan_skills())["reflect-rules"] == "unchanged"


def test_kept_skill_is_asked_again_when_the_source_changes(
    install_everything, plan_skills, apply_skills, actions, toolkit_root, claude_skills
):
    install_everything()
    edited = claude_skills / "reflect-rules" / "SKILL.md"
    edited.write_text(edited.read_text() + "\nMy own note.\n")
    plan_skills()
    apply_skills({"reflect-rules": "keep-mine"})
    (toolkit_root / "skills" / "reflect-rules" / "extra.md").write_text("new\n")

    assert actions(plan_skills())["reflect-rules"] == "modified-locally"


def test_foreign_skill_with_same_name_is_a_collision_and_keep_both_renames(
    plan_skills, apply_skills, actions, claude_skills: Path
):
    write_skill(claude_skills / "sync-rules", "sync-rules", "Someone else's skill.")

    plan = plan_skills()
    assert actions(plan)["sync-rules"] == "collision"
    decisions = {"sync-rules": "keep-both", "reflect-rules": "install"}
    assert apply_skills({**decisions, "correct-rules": "install"}) == 0

    assert (
        "Someone else's skill."
        in (claude_skills / "sync-rules" / "SKILL.md").read_text()
    )
    renamed = (claude_skills / "mstack-sync-rules" / "SKILL.md").read_text()
    assert renamed.startswith("---\nname: mstack-sync-rules\n")
    assert (
        claude_skills / "mstack-sync-rules" / "references" / "principles.md"
    ).is_file()
    assert actions(plan_skills())["sync-rules"] == "unchanged"


def test_keep_theirs_replaces_the_foreign_skill_after_a_backup(
    plan_skills, apply_skills, claude_skills: Path
):
    write_skill(claude_skills / "sync-rules", "sync-rules", "Someone else's skill.")
    plan_skills()

    assert (
        apply_skills({
            "sync-rules": "keep-theirs",
            "reflect-rules": "skip",
            "correct-rules": "skip",
        })
        == 0
    )

    assert "Sync prose rules" in (claude_skills / "sync-rules" / "SKILL.md").read_text()
    backups = list((claude_skills / ".mstack-backups").glob("*/sync-rules/SKILL.md"))
    assert len(backups) == 1
    assert "Someone else's skill." in backups[0].read_text()


def test_pstack_reflect_is_proposed_as_similar(plan_skills, claude_skills: Path):
    write_skill(
        claude_skills / "reflect",
        "reflect",
        "Mine the transcript for learnings and route them into skills.",
    )

    items = {item["id"]: item for item in plan_skills()["items"]}

    similar = items["reflect-rules"]["similar_to"]
    assert [match["name"] for match in similar] == ["reflect"]
    assert similar[0]["score"] == pytest.approx(1.0)
    assert "known overlap" in similar[0]["reason"]
    assert similar[0]["path"] == str(claude_skills / "reflect")
    assert items["sync-rules"]["similar_to"] == []


def test_merged_folder_is_installed_and_its_hash_recorded(
    setup_module,
    plan_skills,
    apply_skills,
    actions,
    claude_skills: Path,
    work_directory: Path,
):
    write_skill(claude_skills / "reflect-rules", "reflect-rules", "My reflect.")
    merged = work_directory / "merged" / "reflect-rules"
    write_skill(merged, "reflect-rules", "Merged reflect.")
    (merged / "notes.md").write_text("from both sides\n")
    plan_skills()

    assert (
        apply_skills({
            "reflect-rules": f"merged:{merged}",
            "sync-rules": "install",
            "correct-rules": "install",
        })
        == 0
    )

    assert (claude_skills / "reflect-rules" / "notes.md").is_file()
    manifest = json.loads((claude_skills / ".mstack-manifest.json").read_text())
    entry = manifest["skills"]["reflect-rules"]
    assert entry["hash"] == setup_module.digest(setup_module.read_skill(merged))
    assert entry["state"] == "merged"
    assert actions(plan_skills())["reflect-rules"] == "unchanged"


def test_merged_folder_with_another_name_is_refused(
    plan_skills, apply_skills, claude_skills: Path, work_directory: Path
):
    write_skill(claude_skills / "reflect-rules", "reflect-rules", "My reflect.")
    merged = work_directory / "merged" / "reflect-rules"
    write_skill(merged, "something-else", "Merged reflect.")
    plan_skills()

    assert (
        apply_skills({
            "reflect-rules": f"merged:{merged}",
            "sync-rules": "skip",
            "correct-rules": "skip",
        })
        == 1
    )
    assert "My reflect." in (claude_skills / "reflect-rules" / "SKILL.md").read_text()


def test_old_symlink_is_migrated_to_a_copy(
    plan_skills, apply_skills, actions, toolkit_root: Path, claude_skills: Path
):
    claude_skills.mkdir(parents=True)
    (claude_skills / "sync-rules").symlink_to(toolkit_root / "skills" / "sync-rules")

    assert actions(plan_skills())["sync-rules"] == "migrate-symlink"
    assert apply_skills(dict.fromkeys(SKILL_NAMES, "install")) == 0

    assert not (claude_skills / "sync-rules").is_symlink()
    assert (claude_skills / "sync-rules" / "SKILL.md").is_file()
    assert (toolkit_root / "skills" / "sync-rules" / "SKILL.md").is_file()


def test_both_tools_write_only_the_claude_folder(
    install_everything, claude_skills: Path, cursor_skills: Path
):
    install_everything("claude,cursor")

    assert sorted(path.name for path in claude_skills.iterdir()) == [
        ".mstack-manifest.json",
        *SKILL_NAMES,
    ]
    assert not cursor_skills.exists()


def test_both_tools_report_the_cursor_copy_as_duplicate(
    install_everything,
    plan_skills,
    apply_skills,
    actions,
    claude_skills: Path,
    cursor_skills: Path,
):
    install_everything("cursor")

    plan = plan_skills("claude,cursor")
    duplicates = {f"{name}@~/.cursor/skills": "duplicate" for name in SKILL_NAMES}
    assert actions(plan) == {**dict.fromkeys(SKILL_NAMES, "install"), **duplicates}
    decisions = {
        **dict.fromkeys(SKILL_NAMES, "install"),
        **dict.fromkeys(duplicates, "remove-duplicate"),
    }
    assert apply_skills(decisions) == 0

    assert [path.name for path in cursor_skills.iterdir()] == [".mstack-backups"]
    assert all((claude_skills / name).is_dir() for name in SKILL_NAMES)
    assert all(
        item["action"] == "unchanged" for item in plan_skills("claude,cursor")["items"]
    )


def test_backups_never_land_next_to_the_skills(
    install_everything,
    plan_skills,
    apply_skills,
    toolkit_root: Path,
    claude_skills: Path,
):
    install_everything()
    (toolkit_root / "skills" / "sync-rules" / "SKILL.md").write_text(
        "---\nname: sync-rules\ndescription: changed\n---\n"
    )
    plan_skills()

    assert apply_skills({"sync-rules": "update"}) == 0

    assert sorted(path.name for path in claude_skills.iterdir()) == [
        ".mstack-backups",
        ".mstack-manifest.json",
        *SKILL_NAMES,
    ]
    assert list((claude_skills / ".mstack-backups").glob("*/sync-rules/SKILL.md"))


def test_corrupt_manifest_overwrites_nothing(
    install_everything,
    plan_skills,
    apply_skills,
    actions,
    toolkit_root: Path,
    claude_skills: Path,
):
    install_everything()
    (claude_skills / ".mstack-manifest.json").write_text("{not json")
    (toolkit_root / "skills" / "sync-rules" / "SKILL.md").write_text(
        "---\nname: sync-rules\ndescription: changed\n---\n"
    )
    installed = (claude_skills / "sync-rules" / "SKILL.md").read_text()

    plan = plan_skills()
    assert plan["manifest"] == "corrupt"
    assert actions(plan)["sync-rules"] == "modified-locally"
    assert apply_skills({"sync-rules": "update"}) == 1
    assert apply_skills({}) == 1
    assert apply_skills({"sync-rules": "skip"}) == 0
    assert (claude_skills / "sync-rules" / "SKILL.md").read_text() == installed


def test_dry_run_writes_nothing(
    plan_skills,
    apply_skills,
    toolkit_root: Path,
    claude_skills: Path,
    home_directory: Path,
):
    write_skill(claude_skills / "sync-rules", "sync-rules", "Someone else's skill.")
    (claude_skills / "correct-rules").symlink_to(
        toolkit_root / "skills" / "correct-rules"
    )
    before = snapshot(home_directory)
    plan_skills()

    assert (
        apply_skills(
            {
                "sync-rules": "keep-theirs",
                "reflect-rules": "install",
                "correct-rules": "install",
            },
            "--dry-run",
        )
        == 0
    )

    assert snapshot(home_directory) == before


def test_stale_plan_is_refused(plan_skills, apply_skills, claude_skills: Path):
    plan_skills()
    write_skill(claude_skills / "sync-rules", "sync-rules", "Appeared after the plan.")

    assert apply_skills(dict.fromkeys(SKILL_NAMES, "install")) == 1
    assert (
        "Appeared after the plan."
        in (claude_skills / "sync-rules" / "SKILL.md").read_text()
    )


def test_toolkit_config_is_written_and_resolves_the_toolkit(
    install_everything, toolkit_resolver: str, toolkit_root: Path, home_directory: Path
):
    install_everything()

    config = json.loads(
        (home_directory / ".config" / "mstack" / "config.json").read_text()
    )
    assert config == {
        "toolkit_path": str(toolkit_root),
        "targets": [str(home_directory / ".claude" / "skills")],
    }
    resolved = subprocess.run(
        ["bash", "-c", toolkit_resolver],
        env={"HOME": str(home_directory), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert resolved.returncode == 0, resolved.stderr
    assert resolved.stdout.strip() == str(toolkit_root)


def test_mstack_home_takes_priority_over_the_config(
    toolkit_resolver: str, toolkit_root: Path, home_directory: Path
):
    resolved = subprocess.run(
        ["bash", "-c", toolkit_resolver],
        env={
            "HOME": str(home_directory),
            "MSTACK_HOME": str(toolkit_root),
            "PATH": "/usr/bin:/bin",
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert resolved.stdout.strip() == str(toolkit_root)


def test_toolkit_resolution_fails_clearly_without_either(
    toolkit_resolver: str, home_directory: Path
):
    resolved = subprocess.run(
        ["bash", "-c", toolkit_resolver],
        env={"HOME": str(home_directory), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert resolved.returncode == 1
    assert "set MSTACK_HOME" in resolved.stderr


def test_verify_passes_after_install_and_reports_missing_references(
    setup_module, install_everything, capsys, claude_skills: Path
):
    install_everything()
    capsys.readouterr()

    assert setup_module.main(["skills", "verify", "--tools", "claude", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["problems"] == []
    (claude_skills / "sync-rules" / "references" / "principles.md").unlink()
    (claude_skills / "sync-rules" / "references").rmdir()
    assert setup_module.main(["skills", "verify", "--tools", "claude", "--json"]) == 1
    problems = json.loads(capsys.readouterr().out)["problems"]
    assert "reflect-rules: ../sync-rules/references/ does not resolve" in problems


def test_missing_manifest_where_mstack_installed_before_overwrites_nothing(
    install_everything, plan_skills, actions, toolkit_root: Path, claude_skills: Path
):
    install_everything()
    (claude_skills / ".mstack-manifest.json").unlink()
    (toolkit_root / "skills" / "sync-rules" / "SKILL.md").write_text(
        "---\nname: sync-rules\ndescription: changed\n---\n"
    )

    plan = plan_skills()

    assert plan["manifest"] == "missing"
    assert actions(plan)["sync-rules"] == "modified-locally"
    assert actions(plan)["reflect-rules"] == "unchanged"


def test_project_level_symlinks_are_reported_as_duplicates(
    plan_skills, apply_skills, actions, toolkit_root: Path
):
    project_skills = toolkit_root / ".cursor" / "skills"
    project_skills.mkdir(parents=True)
    (project_skills / "sync-rules").symlink_to(toolkit_root / "skills" / "sync-rules")

    plan = plan_skills()
    identifier = f"sync-rules@{project_skills}"

    assert actions(plan)[identifier] == "duplicate"
    assert (
        apply_skills({
            **dict.fromkeys(SKILL_NAMES, "install"),
            identifier: "remove-duplicate",
        })
        == 0
    )
    assert not (project_skills / "sync-rules").is_symlink()
    assert (toolkit_root / "skills" / "sync-rules" / "SKILL.md").is_file()
