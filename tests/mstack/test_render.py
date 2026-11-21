from pathlib import Path

import pytest

from mstack.render import FrontmatterError, render_rule, split_frontmatter
from tests.conftest import REPOSITORY_ROOT

RULE_FILES = sorted((REPOSITORY_ROOT / "rules").glob("*.mdc"))


@pytest.mark.parametrize("mdc", RULE_FILES, ids=[path.stem for path in RULE_FILES])
def test_every_repository_rule_renders_as_the_skill_describes(
    mdc: Path, expected_rendering
):
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
