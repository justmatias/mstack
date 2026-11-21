import re
import subprocess
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PINNED_VERSION_PATTERN = re.compile(
    r"(?:rev: v|justmatias/mstack@v)(\d+\.\d+\.\d+)",
)
DOCUMENTS_WITH_PINNED_VERSIONS = ("README.md", "docs/workflow.md")


def project_version() -> str:
    pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text())
    return pyproject["project"]["version"]


def test_docs_pin_the_project_version_when_a_release_was_made() -> None:
    expected = project_version()
    for document in DOCUMENTS_WITH_PINNED_VERSIONS:
        text = (REPOSITORY_ROOT / document).read_text()
        pinned = PINNED_VERSION_PATTERN.findall(text)
        assert pinned, f"{document} pins no mstack version"
        assert set(pinned) == {expected}, (
            f"{document} pins {set(pinned)}, not {expected}"
        )


def test_update_script_rewrites_every_pinned_version(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    for document in DOCUMENTS_WITH_PINNED_VERSIONS:
        original = (REPOSITORY_ROOT / document).read_text()
        (tmp_path / document).write_text(original)

    subprocess.run(
        [str(REPOSITORY_ROOT / "scripts/update-version-references.sh")],
        cwd=tmp_path,
        env={"NEW_VERSION": "99.1.2", "PATH": "/usr/bin:/bin"},
        check=True,
    )

    for document in DOCUMENTS_WITH_PINNED_VERSIONS:
        pinned = PINNED_VERSION_PATTERN.findall((tmp_path / document).read_text())
        assert set(pinned) == {"99.1.2"}
