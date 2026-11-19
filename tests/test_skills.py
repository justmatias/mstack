import re

import pytest

from tests.conftest import REPOSITORY_ROOT, read_frontmatter

SKILLS = REPOSITORY_ROOT / "skills"
ON_REQUEST_SKILLS = {"reflect-rules", "correct-rules"}
TRIGGER_PHRASES = {
    "sync-rules": [
        "sync the rules",
        "after editing .cursor/rules",
        "--check",
        "--user",
    ],
    "reflect-rules": ["reflect-rules", "transcript", "personal"],
    "correct-rules": ["/correct-rules", "keep repeating", "real past mistake"],
}
PRINCIPLES_HEADER = re.compile(r"English only.*Practices, not domain", re.DOTALL)


@pytest.mark.parametrize("skill", sorted(TRIGGER_PHRASES))
def test_skill_frontmatter_is_valid(skill: str):
    frontmatter = read_frontmatter(SKILLS / skill / "SKILL.md")

    assert frontmatter["name"] == skill
    assert all(
        phrase in frontmatter["description"] for phrase in TRIGGER_PHRASES[skill]
    )
    assert frontmatter.get("disable-model-invocation", False) is (
        skill in ON_REQUEST_SKILLS
    )


@pytest.mark.parametrize("skill", sorted(ON_REQUEST_SKILLS))
def test_adapted_skills_reference_notices(skill: str):
    last_line = (SKILLS / skill / "SKILL.md").read_text().rstrip().splitlines()[-1]

    assert (
        last_line
        == f"Adapted from pstack/{skill.removesuffix('-rules')} (MIT). See THIRD_PARTY_NOTICES.md"
    )
    assert (SKILLS / "THIRD_PARTY_NOTICES.md").is_file()


@pytest.mark.parametrize(
    "document",
    sorted(
        path for path in SKILLS.rglob("*.md") if path.name != "THIRD_PARTY_NOTICES.md"
    ),
    ids=lambda path: str(path.relative_to(SKILLS)),
)
def test_every_skill_document_states_both_principles(document):
    head = "\n".join(document.read_text().splitlines()[:12])

    assert PRINCIPLES_HEADER.search(head)


@pytest.mark.parametrize(
    "reference", ["rule-format.md", "authoring-a-check.md", "discovery.md"]
)
def test_shared_references_are_reachable_from_every_skill(reference: str):
    for skill in ("reflect-rules", "correct-rules"):
        assert (
            f"../sync-rules/references/{reference}"
            in (SKILLS / skill / "SKILL.md").read_text()
        )
