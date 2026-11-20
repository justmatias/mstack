import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import mstack.doctor
from mstack.doctor import main
from mstack.doctor.cli import check_cli
from mstack.doctor.drift import check_drift
from mstack.doctor.platform import check_platform
from mstack.doctor.rules import check_rules
from mstack.doctor.skills import check_skills_installed
from mstack.doctor.tools import check_tools
from mstack.doctor.version import check_version
from mstack.install.item_kinds import Kind
from mstack.install.manifest import (
    Manifest,
    manifest_path,
    record_item,
    save_manifest,
)
from tests.mstack.conftest import git


def statuses(results) -> dict[tuple[str, str], str]:
    return {(result.group, result.check): result.status for result in results}


def test_nothing_installed_reports_missing_skills_and_rules(context):
    results = check_skills_installed(context()) + check_rules(context())

    assert statuses(results) == {
        ("skills", "installed"): "error",
        ("rules", "installed"): "error",
    }
    assert all(result.fix for result in results)


@pytest.mark.usefixtures("installed_home")
def test_installed_skills_and_rules_pass(context):
    results = check_skills_installed(context()) + check_rules(context())

    assert set(statuses(results).values()) == {"ok"}


def test_duplicate_skill_in_both_tools_warns(context, installed_home: Path):
    shutil.copytree(
        installed_home / ".claude" / "skills" / "sync",
        installed_home / ".cursor" / "skills" / "sync",
    )

    results = check_skills_installed(context(tool="both"))

    assert statuses(results)[("skills", "duplicates")] == "warn"


def test_broken_skill_is_an_error(context, installed_home: Path):
    skill = installed_home / ".claude" / "skills" / "sync" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    skill.write_text(text.replace("name: sync", "name: other"), encoding="utf-8")

    results = check_skills_installed(context())

    assert statuses(results)[("skills", "valid")] == "error"


def test_rule_with_frontmatter_is_an_error(context, installed_home: Path):
    rule = installed_home / ".claude" / "rules" / "logging.md"
    text = rule.read_text(encoding="utf-8")
    rule.write_text("---\nalwaysApply: true\n---\n" + text, encoding="utf-8")

    results = check_rules(context())

    assert statuses(results) == {("rules", "frontmatter"): "error"}


def test_cursor_only_skips_claude_rules(context):
    assert not check_rules(context(tool="cursor"))
    detail = check_skills_installed(context(tool="cursor"))[0].detail
    assert str(Path(".cursor") / "skills") in detail


def record(checkout: Path, kind: Kind, name: str, target: Path) -> None:
    path = manifest_path()
    manifest = Manifest()
    if path.is_file():
        manifest = Manifest.model_validate_json(path.read_text(encoding="utf-8"))
    record_item(manifest, kind, name, target, checkout)
    save_manifest(manifest, path)


def edit(path: Path) -> None:
    path.write_text(path.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")


def apply_drift(state: str, checkout: Path, home: Path) -> None:
    skill = home / ".claude" / "skills" / "sync"
    if state != "unknown":
        record(checkout, "skill", "sync", skill)
    if state in {"locally-edited", "conflict"}:
        edit(skill / "SKILL.md")
    if state in {"upstream-changed", "conflict"}:
        edit(checkout / "skills" / "sync" / "SKILL.md")
    if state == "unknown":
        # Installed and different from upstream, but never recorded.
        record(checkout, "rule", "logging", home / ".claude/rules/logging.md")
        edit(skill / "SKILL.md")
    if state == "removed":
        shutil.rmtree(skill)


@pytest.mark.usefixtures("installed_home")
@pytest.mark.parametrize(
    "state", ["locally-edited", "upstream-changed", "conflict", "removed", "unknown"]
)
def test_every_drift_state_warns(context, checkout: Path, home: Path, state: str):
    apply_drift(state, checkout, home)

    results = check_drift(context())

    assert [
        (result.check, result.status, result.detail.split()[0]) for result in results
    ] == [("skill sync", "warn", state)]


@pytest.mark.usefixtures("installed_home")
def test_identical_items_pass_drift(context, checkout: Path, home: Path):
    record(checkout, "skill", "sync", home / ".claude/skills/sync")

    results = check_drift(context())

    assert [result.status for result in results] == ["ok"]


def test_no_manifest_means_no_drift_check(context):
    assert check_drift(context()) == []


def test_missing_tools(context, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("mstack.doctor.tools.shutil.which", lambda name: None)

    results = check_tools(context())

    assert statuses(results) == {
        ("tools", "uv"): "error",
        ("tools", "git"): "error",
        ("tools", "gh"): "warn",
    }


def test_mstack_missing_from_path(context, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("mstack.doctor.cli.shutil.which", lambda name: None)

    results = check_cli(context())

    assert statuses(results)[("cli", "mstack")] == "error"
    assert (results[0].fix or "").startswith("uv tool install --editable")


@pytest.mark.skipif(sys.platform == "win32", reason="runs a POSIX shell script")
def test_mstack_on_path_with_another_version(
    context, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    other = tmp_path / "bin" / "mstack"
    other.parent.mkdir()
    other.write_text("#!/bin/sh\necho 'mstack 0.0.1'\n")
    other.chmod(0o755)
    monkeypatch.setattr("mstack.doctor.cli.shutil.which", lambda name: str(other))

    results = check_cli(context())

    assert statuses(results) == {("cli", "mstack"): "error", ("cli", "ast-grep"): "ok"}
    assert "0.0.1" in results[0].detail


def run_doctor(capsys, *arguments: str) -> tuple[int, dict]:
    exit_code = main(["--json", *arguments])
    return exit_code, json.loads(capsys.readouterr().out)


@pytest.mark.usefixtures("home")
def test_json_report_and_exit_code_when_nothing_is_installed(capsys, checkout: Path):
    exit_code, report = run_doctor(capsys, "--checkout", str(checkout))

    assert exit_code == 1
    assert report["ok"] is False
    assert report["tool"] == "claude"
    assert {tuple(sorted(result)) for result in report["results"]} == {
        ("check", "detail", "fix", "group", "status")
    }


@pytest.mark.usefixtures("installed_home")
def test_exit_code_is_zero_after_setup(capsys, checkout: Path, monkeypatch):
    # The CLI on PATH depends on the machine running the tests; it is tested above.
    monkeypatch.setattr(
        mstack.doctor,
        "CHECKS",
        [check for check in mstack.doctor.CHECKS if check is not check_cli],
    )

    exit_code, report = run_doctor(capsys, "--checkout", str(checkout))

    assert exit_code == 0, report
    assert report["ok"] is True


def test_default_tool_follows_the_existing_folders(capsys, checkout: Path, home: Path):
    (home / ".cursor").mkdir()

    _, report = run_doctor(capsys, "--checkout", str(checkout))

    assert report["tool"] == "cursor"


@pytest.fixture
def origin_with_tag(checkout: Path, tmp_path: Path):
    def tag(version: str) -> None:
        origin = tmp_path / "origin.git"
        subprocess.run(["git", "init", "--quiet", "--bare", str(origin)], check=True)
        git(checkout, "remote", "add", "origin", str(origin))
        git(checkout, "tag", version)
        git(checkout, "push", "--quiet", "origin", "--tags")

    return tag


def test_online_reports_a_newer_release(context, origin_with_tag):
    origin_with_tag("v999.0.0")

    results = check_version(context(online=True))

    assert statuses(results) == {("version", "latest"): "warn"}
    assert "v999.0.0" in results[0].detail


def test_online_passes_on_the_latest_release(context, origin_with_tag):
    origin_with_tag("v0.0.1")

    assert statuses(check_version(context(online=True))) == {
        ("version", "latest"): "ok"
    }


def test_no_network_without_online(context, monkeypatch: pytest.MonkeyPatch):
    def fail(*_arguments, **_keywords):
        raise AssertionError("doctor used git ls-remote without --online")

    monkeypatch.setattr("mstack.doctor.version.subprocess.run", fail)

    assert not check_version(context())


@pytest.mark.usefixtures("installed_home")
def test_wsl_with_both_tools_checks_each_tools_skills(context, tmp_path):
    windows = tmp_path / "windows"

    results = check_skills_installed(
        context(tool="both", platform="wsl", cursor_home=windows)
    )

    installed = [result for result in results if result.check == "installed"]
    assert [result.status for result in installed] == ["ok", "error"]
    assert str(windows / ".cursor" / "skills") in installed[1].detail


def test_wsl_without_windows_profile_warns(context):
    results = check_platform(context(tool="cursor", platform="wsl"))

    assert statuses(results) == {("platform", "wsl-cursor"): "warn"}


def test_platform_check_is_silent_outside_wsl(context):
    assert not check_platform(context(tool="cursor"))
