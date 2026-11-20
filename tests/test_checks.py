from pathlib import Path

import pytest

from tests.conftest import REPOSITORY_ROOT

VALID_DIRECTORY = REPOSITORY_ROOT / "fixtures" / "valid"
INVALID_DIRECTORY = REPOSITORY_ROOT / "fixtures" / "invalid"
INVALID_FILES = sorted(INVALID_DIRECTORY.rglob("*.py"))


def test_valid_fixtures_have_no_errors(scan_findings):
    findings = scan_findings(VALID_DIRECTORY)

    assert [finding for finding in findings if finding["severity"] == "error"] == []


@pytest.mark.parametrize(
    "invalid_file",
    INVALID_FILES,
    ids=lambda path: str(path.relative_to(INVALID_DIRECTORY)),
)
def test_every_invalid_fixture_is_caught(scan_findings, invalid_file: Path):
    assert scan_findings(invalid_file) != []
