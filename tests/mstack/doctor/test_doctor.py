import shutil
import sys
from pathlib import Path

import pytest

import mstack.doctor
from mstack.doctor.cli import check_cli
from mstack.doctor.drift import check_drift
from mstack.doctor.platform import check_platform
from mstack.doctor.rules import check_rules
from mstack.doctor.skills import check_skills_installed
from mstack.doctor.targets import skill_sources
from mstack.doctor.tools import check_tools
from mstack.doctor.version import check_version
from tests.mstack.doctor.helpers import append_line, drift_rows, run_doctor, statuses


def test_doctor_reports_missing_skills_and_rules_when_nothing_is_installed(context):
    results = check_skills_installed(context()) + check_rules(context())

    assert statuses(results) == {
        ("skills", "installed"): "error",
        ("rules", "installed"): "error",
    }
    assert all(result.fix for result in results)


@pytest.mark.usefixtures("installed_home")
def test_doctor_passes_when_skills_and_rules_are_installed(context):
    results = check_skills_installed(context()) + check_rules(context())

    assert set(statuses(results).values()) == {"ok"}


def test_doctor_warns_when_both_tools_have_the_same_skill(
    context, installed_home: Path
):
    shutil.copytree(
        installed_home / ".claude" / "skills" / "sync",
        installed_home / ".cursor" / "skills" / "sync",
    )

    results = check_skills_installed(context(tool="both"))

    assert statuses(results)[("skills", "duplicates")] == "warn"


def test_doctor_reports_an_error_when_a_skill_is_broken(context, installed_home: Path):
    skill = installed_home / ".claude" / "skills" / "sync" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    skill.write_text(text.replace("name: sync", "name: other"), encoding="utf-8")

    results = check_skills_installed(context())

    assert statuses(results)[("skills", "valid")] == "error"


def test_doctor_reports_an_error_when_a_rule_keeps_its_frontmatter(
    context, installed_home: Path
):
    rule = installed_home / ".claude" / "rules" / "error-handling.md"
    text = rule.read_text(encoding="utf-8")
    rule.write_text("---\nalwaysApply: true\n---\n" + text, encoding="utf-8")

    results = check_rules(context())

    assert statuses(results) == {("rules", "frontmatter"): "error"}


def test_doctor_skips_claude_rules_when_only_cursor_is_used(context):
    assert not check_rules(context(tool="cursor"))
    detail = check_skills_installed(context(tool="cursor"))[0].detail
    assert str(Path(".cursor") / "skills") in detail


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
def test_drift_ignores_files_when_they_are_backups_or_caches(context, home: Path):
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


def test_drift_skips_items_when_they_are_not_installed(context):
    assert drift_rows(check_drift(context())) == [("checkout", "ok")]


def test_tools_check_reports_each_tool_when_it_is_missing(
    context, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("mstack.doctor.tools.shutil.which", lambda name: None)

    results = check_tools(context())

    assert statuses(results) == {
        ("tools", "uv"): "error",
        ("tools", "git"): "error",
        ("tools", "gh"): "warn",
    }


def test_cli_check_fails_when_mstack_is_missing_from_path(
    context, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("mstack.doctor.cli.shutil.which", lambda name: None)

    results = check_cli(context())

    assert statuses(results)[("cli", "mstack")] == "error"
    assert (results[0].fix or "").startswith("uv tool install --editable")


@pytest.mark.skipif(sys.platform == "win32", reason="runs a POSIX shell script")
def test_cli_check_fails_when_mstack_on_path_has_another_version(
    context, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    other = tmp_path / "bin" / "mstack"
    other.parent.mkdir()
    other.write_text("#!/bin/sh\necho 'mstack 0.0.1'\n")
    other.chmod(0o755)
    monkeypatch.setattr("mstack.doctor.cli.shutil.which", lambda name: str(other))

    results = check_cli(context())

    assert statuses(results) == {("cli", "mstack"): "error", ("cli", "rulepack"): "ok"}
    assert "0.0.1" in results[0].detail


def test_rulepack_check_fails_with_pinned_install_when_rulepack_is_missing(
    context, checkout: Path, monkeypatch: pytest.MonkeyPatch
):
    (checkout / "pyproject.toml").write_text(
        '[tool.mstack]\nrulepack = "v9.9.9"\n', encoding="utf-8"
    )
    monkeypatch.setattr(
        "mstack.doctor.cli.shutil.which",
        lambda name: None if name == "rulepack" else name,
    )

    results = check_cli(context())

    rulepack = next(result for result in results if result.check == "rulepack")
    assert rulepack.status == "error"
    assert rulepack.fix == (
        "uv tool install git+https://github.com/justmatias/rulepack@v9.9.9"
    )


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
def test_doctor_exits_zero_when_setup_is_complete(capsys, checkout: Path, monkeypatch):
    # The CLI on PATH depends on the machine running the tests; it is tested above.
    monkeypatch.setattr(
        mstack.doctor,
        "CHECKS",
        [check for check in mstack.doctor.CHECKS if check is not check_cli],
    )

    exit_code, report = run_doctor(capsys, "--checkout", str(checkout))

    assert exit_code == 0, report
    assert report["ok"] is True


def test_doctor_picks_the_tool_when_only_its_folders_exist(
    capsys, checkout: Path, home: Path
):
    (home / ".cursor").mkdir()

    _, report = run_doctor(capsys, "--checkout", str(checkout))

    assert report["tool"] == "cursor"


def test_version_check_warns_when_a_newer_release_exists(context, origin_with_tag):
    origin_with_tag("v999.0.0")

    results = check_version(context(online=True))

    assert statuses(results) == {("version", "latest"): "warn"}
    assert "v999.0.0" in results[0].detail


def test_version_check_passes_when_checkout_is_on_the_latest_release(
    context, origin_with_tag
):
    origin_with_tag("v0.0.1")

    assert statuses(check_version(context(online=True))) == {
        ("version", "latest"): "ok"
    }


def test_version_check_uses_no_network_when_online_is_not_set(
    context, monkeypatch: pytest.MonkeyPatch
):
    def fail(*_arguments, **_keywords):
        raise AssertionError("doctor used git ls-remote without --online")

    monkeypatch.setattr("mstack.doctor.version.subprocess.run", fail)

    assert not check_version(context())


@pytest.mark.usefixtures("installed_home")
def test_doctor_checks_each_tools_skills_when_wsl_has_both_tools(context, tmp_path):
    windows = tmp_path / "windows"

    results = check_skills_installed(
        context(tool="both", platform="wsl", cursor_home=windows)
    )

    installed = [result for result in results if result.check == "installed"]
    assert [result.status for result in installed] == ["ok", "error"]
    assert str(windows / ".cursor" / "skills") in installed[1].detail


def test_platform_check_warns_when_wsl_has_no_windows_profile(context):
    results = check_platform(context(tool="cursor", platform="wsl"))

    assert statuses(results) == {("platform", "wsl-cursor"): "warn"}


def test_platform_check_is_silent_when_not_on_wsl(context):
    assert not check_platform(context(tool="cursor"))
