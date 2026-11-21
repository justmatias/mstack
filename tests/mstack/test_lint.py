import shutil
import sys
import sysconfig
from pathlib import Path

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
