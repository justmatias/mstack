from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT

DEMO_DIRECTORY = REPOSITORY_ROOT / "demo" / "violations"
AST_GREP_DEMO_FILES = sorted(
    path
    for path in DEMO_DIRECTORY.glob("*.py")
    if path.name != "domain_imports_infra.py"
)


def test_example_app_has_no_errors(scan_findings):
    findings = scan_findings(REPOSITORY_ROOT / "example_app")

    assert [finding for finding in findings if finding["severity"] == "error"] == []


@pytest.mark.parametrize("demo_file", AST_GREP_DEMO_FILES, ids=lambda path: path.name)
def test_every_demo_file_is_caught(scan_findings, demo_file: Path):
    assert scan_findings(demo_file) != []


def test_lint_imports_passes_on_example_app(run_lint_imports, repository_root: Path):
    assert run_lint_imports(repository_root).returncode == 0


def test_lint_imports_fails_when_domain_imports_infra(
    run_lint_imports, import_linter_sandbox: Path
):
    (
        import_linter_sandbox / "example_app" / "domain" / "domain_imports_infra.py"
    ).write_text((DEMO_DIRECTORY / "domain_imports_infra.py").read_text())

    completed = run_lint_imports(import_linter_sandbox)

    assert completed.returncode != 0
    assert "domain-is-pure BROKEN" in completed.stdout
