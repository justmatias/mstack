import sys

import pytest
import yaml

from tests.conftest import REPOSITORY_ROOT
from tests.helpers import run_command


@pytest.fixture
def run_mstack():
    def run(command: str, *arguments: str):
        return run_command(
            [sys.executable, "-m", "mstack", command, *arguments], REPOSITORY_ROOT
        )

    return run


@pytest.fixture
def expected_rendering():
    """The conversion setup-mstack step 3 describes, written independently."""

    def credit(frontmatter: str) -> str:
        metadata = (yaml.safe_load(frontmatter) or {}).get("metadata") or {}
        if "adapted-from" not in metadata:
            return ""
        return (
            f"\n\nAdapted from {metadata['adapted-from']} "
            f"License: {metadata['upstream-license']}."
        )

    def expected(mdc_text: str) -> str:
        _, frontmatter, body = mdc_text.split("---\n", 2)
        globs_line = next(
            (line for line in frontmatter.splitlines() if line.startswith("globs:")),
            None,
        )
        body = body.split("## Checks")[0].strip() + credit(frontmatter)
        if globs_line is None:
            return f"{body}\n"
        globs = globs_line.removeprefix("globs:").strip().strip('"')
        return f"Applies to files matching `{globs}`.\n\n{body}\n"

    return expected
