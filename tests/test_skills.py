import json
import re

import pytest

from tests.conftest import REPOSITORY_ROOT, read_frontmatter

SKILLS = REPOSITORY_ROOT / "skills"
SETUP_SKILL = REPOSITORY_ROOT / ".claude" / "skills" / "setup-mstack"
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
SETUP_TRIGGER_PHRASES = ["set up mstack", "install mstack", "update mstack skills"]
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
        path
        for path in (*SKILLS.rglob("*.md"), *SETUP_SKILL.rglob("*.md"))
        if path.name != "THIRD_PARTY_NOTICES.md"
    ),
    ids=lambda path: str(path.relative_to(REPOSITORY_ROOT)),
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


def test_setup_skill_frontmatter_is_valid():
    frontmatter = read_frontmatter(SETUP_SKILL / "SKILL.md")

    assert frontmatter["name"] == "setup-mstack"
    assert all(phrase in frontmatter["description"] for phrase in SETUP_TRIGGER_PHRASES)


def test_setup_skill_links_to_the_principles():
    text = (SETUP_SKILL / "SKILL.md").read_text()

    link = re.search(r"\]\(([^)]*principles\.md)\)", text)
    assert link is not None
    assert (SETUP_SKILL / link.group(1)).resolve() == (
        SKILLS / "sync-rules" / "references" / "principles.md"
    )


def test_setup_skill_lives_only_in_the_claude_folder():
    assert not (REPOSITORY_ROOT / ".cursor" / "skills" / "setup-mstack").exists()
    assert not (SKILLS / "setup-mstack").exists()


def test_known_overlaps_cover_the_pstack_originals():
    data = json.loads((SETUP_SKILL / "references" / "known-overlaps.json").read_text())

    pairs = {(overlap["skill"], overlap["other"]) for overlap in data["overlaps"]}
    assert {("reflect-rules", "reflect"), ("correct-rules", "correct")} <= pairs
    assert all(overlap["reason"] for overlap in data["overlaps"])
