from pathlib import Path

import pytest

from mstack.install.render import RuleFormatError, render_rule, split_frontmatter
from tests.conftest import REPOSITORY_ROOT

RULE_FILES = sorted((REPOSITORY_ROOT / "rules").glob("*.mdc"))


def expected_rendering(mdc_text: str) -> str:
    """The conversion setup-mstack step 3 describes, written independently."""
    _, frontmatter, body = mdc_text.split("---\n", 2)
    globs_line = next(
        line for line in frontmatter.splitlines() if line.startswith("globs:")
    )
    globs = globs_line.removeprefix("globs:").strip().strip('"')
    body = body.split("## Checks")[0].strip()
    return f"Applies to files matching `{globs}`.\n\n{body}\n"


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
    with pytest.raises(RuleFormatError):
        split_frontmatter("---\ndescription: x\n# Rule\n")
