import json
import shutil
import sys
import sysconfig
from pathlib import Path

import pytest

from mstack.lint import STEPS, find_tool
from tests.conftest import REPOSITORY_ROOT
from tests.mstack.conftest import git

INVALID = REPOSITORY_ROOT / "fixtures" / "invalid"
BARE_EXCEPT = INVALID / "error-handling" / "bare_except.py"
# no-manual-init-boilerplate is a warning: the full scan tolerates it.
MANUAL_INIT = INVALID / "python-models" / "manual_init.py"


def test_clean_repository_passes(run_lint):
    exit_code, report = run_lint()

    assert exit_code == 0, report
    assert list(report) == list(STEPS)
    assert all(step["ok"] for step in report.values())


def test_json_reports_every_step_with_ok_skipped_and_findings(run_lint):
    _, report = run_lint()

    assert {tuple(sorted(step)) for step in report.values()} == {
        ("findings", "ok", "skipped")
    }


def test_invalid_file_fails_scan(run_lint, lint_sandbox: Path):
    shutil.copy(BARE_EXCEPT, lint_sandbox / "fixtures" / "valid" / "zz_scan_target.py")

    exit_code, report = run_lint()

    assert exit_code == 1
    assert not report["scan"]["ok"]
    assert {finding["rule"] for finding in report["scan"]["findings"]} == {
        "no-bare-except"
    }
    assert all(report[step]["ok"] for step in STEPS if step != "scan")


def test_changed_fails_on_a_warning_the_full_scan_tolerates(
    run_lint, lint_sandbox: Path
):
    git(lint_sandbox, "checkout", "--quiet", "-b", "feature")
    shutil.copy(MANUAL_INIT, lint_sandbox / "fixtures" / "valid" / "models.py")

    full_exit_code, full = run_lint("--only", "scan")
    changed_exit_code, changed = run_lint("--only", "scan", "--changed")

    assert (full_exit_code, full["scan"]["ok"]) == (0, True)
    assert (changed_exit_code, changed["scan"]["ok"]) == (1, False)


def test_changed_without_changes_skips_scan(run_lint):
    _, report = run_lint("--only", "scan", "--changed", "--base-ref", "main")

    assert report["scan"]["skipped"] == "no changed files to scan"


def test_files_are_filtered_by_extension(run_lint, lint_sandbox: Path):
    (lint_sandbox / "notes.md").write_text("# Notes\n", encoding="utf-8")

    _, report = run_lint("--only", "scan", "--files", "notes.md")

    assert report["scan"]["skipped"] == "no changed files to scan"


def test_files_scan_fails_on_warnings(run_lint, lint_sandbox: Path):
    shutil.copy(MANUAL_INIT, lint_sandbox / "models.py")

    exit_code, report = run_lint("--only", "scan", "--files", "models.py")

    assert exit_code == 1
    assert {finding["rule"] for finding in report["scan"]["findings"]} == {
        "no-manual-init-boilerplate"
    }


def test_only_runs_the_given_steps(run_lint):
    _, report = run_lint("--only", "coverage", "exceptions")

    assert list(report) == ["coverage", "exceptions"]


def test_skip_leaves_out_the_given_steps(run_lint):
    _, report = run_lint("--skip", "test", "scan")

    assert list(report) == ["imports", "coverage", "exceptions", "domain-check"]


def test_imports_is_skipped_without_importlinter(run_lint, lint_sandbox: Path):
    (lint_sandbox / ".importlinter").unlink(missing_ok=True)

    _, report = run_lint("--only", "imports")

    assert report["imports"] == {
        "ok": True,
        "skipped": "no .importlinter",
        "findings": [],
    }


def test_imports_passes_when_the_contract_is_kept(run_lint, import_contract):
    import_contract(core_imports_adapters=False)

    exit_code, report = run_lint("--only", "imports")

    assert exit_code == 0, report


def test_imports_fails_when_the_contract_is_broken(run_lint, import_contract):
    import_contract(core_imports_adapters=True)

    exit_code, report = run_lint("--only", "imports")

    assert exit_code == 1
    assert any("core-is-pure BROKEN" in line for line in report["imports"]["findings"])


def test_coverage_failure_is_reported_with_its_findings(run_lint, lint_sandbox: Path):
    mdc = lint_sandbox / "rules" / "naming.mdc"
    mdc.write_text(mdc.read_text() + "- enforced-by: no-such-check\n")

    exit_code, report = run_lint("--only", "coverage")

    assert exit_code == 1
    assert any("unknown-check" in finding for finding in report["coverage"]["findings"])


def test_lint_reports_a_missing_source_when_the_prose_folder_is_absent(
    run_lint, lint_sandbox: Path
):
    shutil.rmtree(lint_sandbox / "rules")
    (lint_sandbox / "lint" / "rules" / "no-linked-placeholder.yml").write_text(
        "id: no-linked-placeholder\nlanguage: Python\n"
        "metadata:\n  source: rules/missing.mdc\nrule:\n  kind: pass_statement\n",
        encoding="utf-8",
    )

    exit_code, report = run_lint("--only", "coverage")

    assert exit_code == 1
    assert any(
        "missing-source" in finding for finding in report["coverage"]["findings"]
    )


def test_base_ref_needs_changed(run_mstack, lint_sandbox: Path):
    completed = run_mstack("lint", "--base-ref", "main", working_directory=lint_sandbox)

    assert completed.returncode == 2
    assert "need --changed" in completed.stderr


def test_bundled_ast_grep_is_resolved_first():
    resolved = Path(find_tool("ast-grep")).parent

    assert resolved in {
        Path(sysconfig.get_path("scripts")),
        Path(sys.executable).parent,
    }


@pytest.mark.usefixtures("pack_consumer")
def test_lint_enforces_selected_pack_when_local_rules_are_absent(
    run_mstack, tmp_path: Path
):
    completed = run_mstack("lint", "--json", working_directory=tmp_path)

    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert report["test"]["ok"] and report["test"]["skipped"] is None
    assert report["coverage"]["ok"] and report["coverage"]["skipped"] is None
    assert [finding["rule"] for finding in report["scan"]["findings"]] == [
        "no-bare-except"
    ]
    assert {path.name for path in tmp_path.iterdir()} == {
        ".git",
        ".mstack.toml",
        "target.py",
    }


def test_lint_omits_shared_rule_when_disabled(
    run_mstack, tmp_path: Path, pack_consumer
):
    pack_consumer('[pack_overrides]\ndisable = ["no-bare-except"]\n')

    completed = run_mstack("lint", working_directory=tmp_path)

    assert completed.returncode == 0, completed.stderr


def test_lint_changes_shared_rule_severity_when_overridden(
    run_mstack, tmp_path: Path, pack_consumer
):
    pack_consumer('[pack_overrides]\nseverity = { no-bare-except = "warning" }\n')

    completed = run_mstack("lint", "--json", working_directory=tmp_path)

    assert completed.returncode == 0, completed.stderr
    findings = json.loads(completed.stdout)["scan"]["findings"]
    assert [(item["rule"], item["severity"]) for item in findings] == [
        ("no-bare-except", "warning")
    ]


@pytest.mark.usefixtures("pack_consumer")
def test_lint_uses_local_rule_when_it_shadows_a_shared_rule(run_mstack, tmp_path: Path):
    local = tmp_path / "lint-rules"
    (local / "rules").mkdir(parents=True)
    (local / "sgconfig.yml").write_text("ruleDirs: [rules]\n", encoding="utf-8")
    (local / "rules" / "local.yml").write_text(
        "id: no-bare-except\n"
        "language: Python\n"
        "severity: error\n"
        "message: Local rule\n"
        "rule: {pattern: never_called()}\n",
        encoding="utf-8",
    )

    completed = run_mstack("lint", working_directory=tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert "local check no-bare-except overrides" in completed.stderr


@pytest.mark.usefixtures("pack_consumer")
def test_lint_uses_host_packs_when_repo_has_no_config(
    run_mstack, tmp_path: Path, monkeypatch
):
    (tmp_path / ".mstack.toml").unlink()
    host = tmp_path / ".git" / "mstack"
    host.mkdir()
    (host / "config.toml").write_text('packs = ["python-core"]\n', encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(host.parent))

    completed = run_mstack("lint", "--json", working_directory=tmp_path)

    assert completed.returncode == 1, completed.stderr
    assert any(
        finding["rule"] == "no-bare-except"
        for finding in json.loads(completed.stdout)["scan"]["findings"]
    )


@pytest.mark.usefixtures("pack_consumer")
def test_lint_uses_explicit_packs_when_repo_selects_other_packs(
    run_mstack, tmp_path: Path
):
    completed = run_mstack(
        "lint", "--packs", "testing", "--json", working_directory=tmp_path
    )

    assert completed.returncode == 0, completed.stderr
    assert {
        rule["pack"]
        for rule in json.loads(
            run_mstack("coverage", "--json", working_directory=tmp_path).stdout
        )["rules"]
    } == {"python-core"}
