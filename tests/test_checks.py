from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT

VALID_DIRECTORY = REPOSITORY_ROOT / "fixtures" / "valid"
INVALID_DIRECTORY = REPOSITORY_ROOT / "fixtures" / "invalid"
DOMAIN_IMPORTS_INFRA = (
    INVALID_DIRECTORY / "architecture-layers" / "domain_imports_infra.py"
)
AST_GREP_INVALID_FILES = sorted(
    path
    for path in INVALID_DIRECTORY.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.parts
    and path != DOMAIN_IMPORTS_INFRA
)


def test_valid_fixtures_have_no_errors(scan_findings):
    findings = scan_findings(VALID_DIRECTORY)

    assert [finding for finding in findings if finding["severity"] == "error"] == []


@pytest.mark.parametrize(
    "invalid_file",
    AST_GREP_INVALID_FILES,
    ids=lambda path: str(path.relative_to(INVALID_DIRECTORY)),
)
def test_every_invalid_fixture_is_caught(scan_findings, invalid_file: Path):
    assert scan_findings(invalid_file) != []


def test_lint_imports_passes_on_valid_fixtures(run_lint_imports, repository_root: Path):
    assert run_lint_imports(repository_root).returncode == 0


def test_lint_imports_fails_when_domain_imports_infra(
    run_lint_imports, import_linter_sandbox: Path
):
    (
        import_linter_sandbox
        / "fixtures"
        / "valid"
        / "domain"
        / DOMAIN_IMPORTS_INFRA.name
    ).write_text(DOMAIN_IMPORTS_INFRA.read_text())

    completed = run_lint_imports(import_linter_sandbox)

    assert completed.returncode != 0
    assert "domain-is-pure BROKEN" in completed.stdout
