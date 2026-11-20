import json
import re

import pytest

from tests.conftest import REPOSITORY_ROOT, read_frontmatter

SKILLS = REPOSITORY_ROOT / "skills"
SETUP_SKILL = SKILLS / "setup-mstack"
ON_REQUEST_SKILLS = {"reflect-rules", "correct-rules", "integrate-skills"}
PSTACK_ADAPTED_SKILLS = {"reflect-rules", "correct-rules"}
TRIGGER_PHRASES = {
    "sync-rules": [
        "sync the rules",
        "after editing .cursor/rules",
        "--check",
        "when a rule has no check",
    ],
    "reflect-rules": ["reflect-rules", "transcript", "approval", "--deep"],
    "correct-rules": ["/correct-rules", "keep repeating", "real past mistake"],
    "integrate-skills": ["/integrate-skills", "GitHub URL", "upstream", "approval"],
}
SETUP_TRIGGER_PHRASES = ["set up mstack", "install mstack", "update mstack skills"]
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
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


@pytest.mark.parametrize("skill", sorted(PSTACK_ADAPTED_SKILLS))
def test_adapted_skills_credit_pstack_in_frontmatter(skill: str):
    frontmatter = read_frontmatter(SKILLS / skill / "SKILL.md")
    metadata = frontmatter["metadata"]

    assert frontmatter["license"] == "MIT"
    assert metadata["adapted-from"].startswith(
        f"pstack/skills/{skill.removesuffix('-rules')} in cursor/plugins"
    )
    assert re.fullmatch(r"[0-9a-f]{40}", metadata["upstream-commit"])
    assert "Copyright (c) 2026 Lauren Tan" in metadata["upstream-license"]


@pytest.mark.parametrize(
    "document",
    sorted(SKILLS.rglob("*.md")),
    ids=lambda path: str(path.relative_to(SKILLS)),
)
def test_every_skill_document_states_both_principles(document):
    body = FRONTMATTER.sub("", document.read_text(), count=1)
    head = "\n".join(body.splitlines()[:12])

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


def test_setup_skill_lives_with_the_other_skills():
    assert (SETUP_SKILL / "SKILL.md").is_file()
    assert not (REPOSITORY_ROOT / ".claude" / "skills" / "setup-mstack").exists()
    assert not (REPOSITORY_ROOT / ".cursor" / "skills" / "setup-mstack").exists()


def test_known_overlaps_cover_the_pstack_originals():
    data = json.loads((SETUP_SKILL / "references" / "known-overlaps.json").read_text())

    pairs = {(overlap["skill"], overlap["other"]) for overlap in data["overlaps"]}
    assert {("reflect-rules", "reflect"), ("correct-rules", "correct")} <= pairs
    assert all(overlap["reason"] for overlap in data["overlaps"])


@pytest.mark.parametrize(
    "document",
    sorted(SKILLS.rglob("*.md")),
    ids=lambda path: str(path.relative_to(SKILLS)),
)
def test_skills_run_the_guards_through_the_cli(document):
    text = document.read_text()

    assert "<toolkit>" not in text
    assert ".config/mstack" not in text
    assert "scripts/guards" not in text


@pytest.mark.parametrize(
    "rule",
    sorted((REPOSITORY_ROOT / "rules").glob("*.mdc")),
    ids=lambda path: path.name,
)
def test_every_rule_has_a_description(rule):
    assert read_frontmatter(rule)["description"]
