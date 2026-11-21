import re
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PINNED_REVISION_PATTERN = re.compile(r"rev: v(\d+\.\d+\.\d+)")


def test_readme_pins_the_project_version_when_a_release_was_made() -> None:
    pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    expected = pyproject["project"]["version"]

    pinned = PINNED_REVISION_PATTERN.findall(
        (REPOSITORY_ROOT / "README.md").read_text()
    )

    assert pinned, "README.md pins no mstack revision"
    assert set(pinned) == {expected}
