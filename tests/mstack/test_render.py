from pathlib import Path

import pytest
import yaml

from mstack.render import FrontmatterError, render_rule, split_frontmatter
from tests.conftest import REPOSITORY_ROOT

RULE_FILES = sorted((REPOSITORY_ROOT / "rules").glob("*.mdc"))


def expected_credit(frontmatter: str) -> str:
    metadata = (yaml.safe_load(frontmatter) or {}).get("metadata") or {}
    if "adapted-from" not in metadata:
        return ""
    return f"\n\nAdapted from {metadata['adapted-from']} License: {metadata['upstream-license']}."


def expected_rendering(mdc_text: str) -> str:
    """The conversion setup-mstack step 3 describes, written independently."""
    _, frontmatter, body = mdc_text.split("---\n", 2)
    globs_line = next(
        (line for line in frontmatter.splitlines() if line.startswith("globs:")),
        None,
    )
    body = body.split("## Checks")[0].strip()
    credit = expected_credit(frontmatter)
    if globs_line is None:
        return f"{body}{credit}\n"
    globs = globs_line.removeprefix("globs:").strip().strip('"')
    return f"Applies to files matching `{globs}`.\n\n{body}{credit}\n"


@pytest.mark.parametrize("mdc", RULE_FILES, ids=[path.stem for path in RULE_FILES])
def test_every_repository_rule_renders_as_the_skill_describes(mdc: Path):
    text = mdc.read_text()

    rendered = render_rule(text)

    assert rendered == expected_rendering(text)
    assert not rendered.startswith("---")
    assert "## Checks" not in rendered


def test_rule_without_globs_has_no_applies_line():
    rendered = render_rule("---\ndescription: Always\nalwaysApply: true\n---\n# Rule\n")

    assert rendered == "# Rule\n"


def test_section_after_checks_is_kept():
    rendered = render_rule("# Rule\n\n## Checks\n- enforced-by: x\n\n## Notes\nKeep.\n")

    assert rendered == "# Rule\n\n## Notes\nKeep.\n"


def test_unclosed_frontmatter_is_rejected():
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\ndescription: x\n# Rule\n")


def test_upstream_credit_is_kept_in_the_body_when_frontmatter_is_dropped():
    rendered = render_rule(
        "---\n"
        "license: MIT\n"
        "metadata:\n"
        '  adapted-from: "rules/x.mdc in owner/repo."\n'
        '  upstream-license: "MIT, Copyright (c) Someone"\n'
        '  inspired-by-idea: "https://example.com/idea"\n'
        "---\n# Rule\n"
    )

    assert rendered == (
        "# Rule\n\n"
        "Adapted from rules/x.mdc in owner/repo. "
        "License: MIT, Copyright (c) Someone.\n"
        "Inspired by https://example.com/idea\n"
    )
