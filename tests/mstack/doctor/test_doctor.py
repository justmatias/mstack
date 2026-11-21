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
from mstack.doctor.targets import skill_sources
from mstack.doctor.tools import check_tools
from mstack.doctor.version import check_version
from mstack.render import main as render_main
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
    rule = installed_home / ".claude" / "rules" / "error-handling.md"
    text = rule.read_text(encoding="utf-8")
    rule.write_text("---\nalwaysApply: true\n---\n" + text, encoding="utf-8")

    results = check_rules(context())

    assert statuses(results) == {("rules", "frontmatter"): "error"}


def test_cursor_only_skips_claude_rules(context):
    assert not check_rules(context(tool="cursor"))
    detail = check_skills_installed(context(tool="cursor"))[0].detail
    assert str(Path(".cursor") / "skills") in detail


def append_line(path: Path) -> None:
    path.write_text(path.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")


def drift_rows(results) -> list[tuple[str, str]]:
    return [(result.check, result.status) for result in results]


@pytest.mark.usefixtures("installed_home")
def test_drift_passes_when_every_copy_matches_the_checkout(context):
    assert drift_rows(check_drift(context())) == [("checkout", "ok")]


@pytest.mark.usefixtures("installed_home")
def test_drift_warns_when_the_installed_skill_was_edited(context, home: Path):
    append_line(home / ".claude" / "skills" / "sync" / "SKILL.md")

    results = check_drift(context())

    assert drift_rows(results) == [("skill sync", "warn")]
    assert results[0].fix


@pytest.mark.usefixtures("installed_home")
def test_drift_warns_when_the_checkout_skill_changed(context, checkout: Path):
    (skill_sources(checkout)["sync"] / "references" / "new.md").write_text(
        "New.\n", encoding="utf-8"
    )

    assert drift_rows(check_drift(context())) == [("skill sync", "warn")]


@pytest.mark.usefixtures("installed_home")
def test_drift_warns_when_the_installed_rule_differs_from_the_rendered_one(
    context, home: Path
):
    append_line(home / ".claude" / "rules" / "naming.md")

    assert drift_rows(check_drift(context())) == [("rule naming", "warn")]


@pytest.mark.usefixtures("installed_home")
def test_drift_ignores_backups_and_caches_inside_a_skill(context, home: Path):
    skill = home / ".claude" / "skills" / "sync"
    (skill / "__pycache__").mkdir()
    (skill / "__pycache__" / "module.pyc").write_bytes(b"cache")
    (skill / ".DS_Store").write_bytes(b"finder")

    assert drift_rows(check_drift(context())) == [("checkout", "ok")]


@pytest.mark.usefixtures("installed_home")
def test_drift_warns_when_the_installed_agent_differs(
    context, checkout: Path, home: Path
):
    agent = "---\nname: helper\ndescription: Helps.\n---\n\nHelp.\n"
    (checkout / "agents" / "helper.md").write_text(agent, encoding="utf-8")
    installed = home / ".claude" / "agents" / "helper.md"
    installed.parent.mkdir(parents=True)
    installed.write_text(agent + "Edited.\n", encoding="utf-8")

    assert drift_rows(check_drift(context())) == [("agent helper", "warn")]


def test_drift_skips_items_that_are_not_installed(context):
    assert drift_rows(check_drift(context())) == [("checkout", "ok")]


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


@pytest.fixture
def codex_install(capsys, home, checkout, monkeypatch):
    folder = home / "codex-profile"
    folder.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(folder))
    for name, source in skill_sources(checkout).items():
        shutil.copytree(source, home / ".agents" / "skills" / name)
    (checkout / "instructions" / "global.md").write_text(
        "Global guidance.\n", encoding="utf-8"
    )
    assert render_main(["--combined", str(checkout)]) == 0
    block = capsys.readouterr().out
    (folder / "AGENTS.md").write_text(
        f"Personal guidance.\n\n{block}", encoding="utf-8"
    )
    return folder


def test_codex_doctor_passes_when_the_shared_skills_and_block_match(
    codex_install, capsys, checkout, monkeypatch
):
    monkeypatch.setattr(
        mstack.doctor, "CHECKS", [check_skills_installed, check_rules, check_drift]
    )

    exit_code, report = run_doctor(capsys, "--checkout", str(checkout))

    assert exit_code == 0, report
    assert report["tool"] == "codex"
    assert all(result["status"] == "ok" for result in report["results"])
    text = (codex_install / "AGENTS.md").read_text(encoding="utf-8")
    assert "Global guidance." in text
    assert "Applies to files matching" in text
    assert "## Checks" not in text


def test_codex_rules_reports_a_missing_block_when_an_override_takes_precedence(
    codex_install, context
):
    override = codex_install / "AGENTS.override.md"
    override.write_text("Temporary guidance.\n", encoding="utf-8")

    results = check_rules(context(tool="codex"))

    assert statuses(results) == {("rules", "codex"): "error"}
    assert str(override) in results[0].detail


def test_codex_rule_drift_warns_when_the_managed_block_differs(codex_install, context):
    path = codex_install / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("Global guidance.", "Edited guidance."), encoding="utf-8"
    )

    assert drift_rows(check_drift(context(tool="codex"))) == [("rule codex", "warn")]


@pytest.mark.usefixtures("codex_install")
def test_cursor_shares_the_codex_skills_when_home_matches(context):
    results = check_skills_installed(context(tool="cursor,codex"))

    assert [result.status for result in results if result.check == "installed"] == [
        "ok"
    ]


@pytest.mark.usefixtures("codex_install", "installed_home")
def test_cursor_warns_when_required_claude_and_codex_copies_overlap(context):
    results = check_skills_installed(context(tool="claude,cursor,codex"))

    assert statuses(results)[("skills", "duplicates")] == "warn"


@pytest.mark.usefixtures("codex_install")
def test_cursor_checks_a_separate_copy_when_codex_runs_in_wsl(context, tmp_path):
    windows = tmp_path / "windows"
    results = check_skills_installed(
        context(tool="cursor,codex", platform="wsl", cursor_home=windows)
    )

    installed = [result for result in results if result.check == "installed"]
    assert [result.status for result in installed] == ["error", "ok"]
    assert str(windows / ".cursor" / "skills") in installed[0].detail


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
