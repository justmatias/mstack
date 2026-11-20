import json
from pathlib import Path

import pytest

PRINCIPLES_LINE = "> **Principles (always apply):**"


def test_repository_skills_pass_without_warnings(run_mstack, skills_sandbox: Path):
    completed = run_mstack("skills-check", str(skills_sandbox), "--json")
    report = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert report["issues"] == []
    assert "sync-rules" in report["skills"]


def test_renamed_folder_fails_the_name_check(run_mstack, skills_sandbox: Path):
    (skills_sandbox / "correct-rules").rename(skills_sandbox / "fix-rules")

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 1
    assert "[name] 'correct-rules' does not match the folder name" in completed.stderr


@pytest.mark.parametrize(
    "case",
    [
        ("---\nname: sync-rules", "name: sync-rules", "[frontmatter] no '---'"),
        ("name: sync-rules", "name: [sync-rules", "[frontmatter] not valid YAML"),
        (
            "name: sync-rules",
            "name: Sync_Rules",
            "[name] 'Sync_Rules' is not kebab-case",
        ),
        ('description: "Sync', 'description: ""\nold: "Sync', "[description] missing"),
        ('description: "Sync', 'description: "' + "x" * 1025, "over 1024"),
        (
            "[discovery](references/discovery.md)",
            "[discovery](references/gone.md)",
            "[links] 'references/gone.md' does not exist",
        ),
        (
            "[discovery](references/discovery.md)",
            "[discovery](../../README.md)",
            "[links] '../../README.md' points outside the skills folder",
        ),
        ("> **Principles (always apply):**", "Principles:", "[principles]"),
        (
            "name: sync-rules",
            "name: sync-rules\nauthor: someone",
            "[keys] unknown frontmatter key 'author'",
        ),
    ],
    ids=[
        "no-frontmatter",
        "bad-yaml",
        "not-kebab-case",
        "empty-description",
        "long-description",
        "broken-link",
        "link-outside",
        "no-principles",
        "unknown-key",
    ],
)
def test_broken_skill_fails(
    run_mstack, skills_sandbox: Path, edit_skill, case: tuple[str, str, str]
):
    old, new, expected_problem = case
    edit_skill("sync-rules/SKILL.md", old, new)

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 1
    assert expected_problem in completed.stderr


@pytest.mark.parametrize(
    "case",
    [
        (
            '  upstream-commit: "e58dd043600587dbaf58ba315e7f2b38373eeb43"\n',
            "",
            "'adapted-from' needs a 'upstream-commit' set to a 40-character sha",
        ),
        (
            '"e58dd043600587dbaf58ba315e7f2b38373eeb43"',
            '"e58dd04"',
            "'adapted-from' needs a 'upstream-commit' set to a 40-character sha",
        ),
        ("license: MIT\n", "", "'adapted-from' without 'license'"),
    ],
    ids=["no-upstream-commit", "short-sha", "no-license"],
)
def test_incomplete_credit_fails(
    run_mstack, skills_sandbox: Path, edit_skill, case: tuple[str, str, str]
):
    old, new, expected_problem = case
    edit_skill("correct-rules/SKILL.md", old, new)

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 1
    assert f"[credit] {expected_problem}" in completed.stderr


def test_license_without_credit_fails(run_mstack, skills_sandbox: Path, edit_skill):
    edit_skill(
        "sync-rules/SKILL.md", "name: sync-rules", "name: sync-rules\nlicense: MIT"
    )

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 1
    assert "[credit] 'license' without 'adapted-from'" in completed.stderr


def test_unlinked_reference_only_warns(run_mstack, skills_sandbox: Path):
    (skills_sandbox / "sync-rules" / "references" / "orphan.md").write_text(
        "# Orphan\n"
    )

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 0, completed.stderr
    assert "orphan.md:1: [unused-files] is linked from nowhere" in completed.stderr


def test_non_ascii_prose_only_warns(run_mstack, skills_sandbox: Path, edit_skill):
    edit_skill(
        "sync-rules/SKILL.md",
        "Keep `.cursor/rules/`",
        'Mantené `código` and "señal" out. Keep `.cursor/rules/`',
    )

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 0, completed.stderr
    assert "[english] non-ASCII letters é" in completed.stderr
    assert "ñ" not in completed.stderr
    assert "ó" not in completed.stderr


def test_links_in_code_are_ignored(run_mstack, skills_sandbox: Path, edit_skill):
    edit_skill(
        "sync-rules/SKILL.md",
        "## Modes",
        "`[x](missing.md)`\n\n```markdown\n[y](missing.md)\n```\n\n## Modes",
    )

    completed = run_mstack("skills-check", str(skills_sandbox))

    assert completed.returncode == 0, completed.stderr


def test_generic_profile_skips_mstack_only_checks(
    run_mstack, skills_sandbox: Path, edit_skill
):
    edit_skill("sync-rules/SKILL.md", PRINCIPLES_LINE, "Principles:")
    edit_skill(
        "correct-rules/SKILL.md",
        '  upstream-commit: "e58dd043600587dbaf58ba315e7f2b38373eeb43"\n',
        "",
    )
    edit_skill("setup-mstack/SKILL.md", "Install the mstack", "Instalá the mstack")
    edit_skill(
        "integrate-skills/SKILL.md",
        "name: integrate-skills",
        "name: integrate-skills\nallowed-tools: Read\nauthor: someone",
    )

    completed = run_mstack(
        "skills-check", str(skills_sandbox), "--profile", "generic", "--json"
    )
    report = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert [(entry["check"], entry["severity"]) for entry in report["issues"]] == [
        ("keys", "warning")
    ]


def test_missing_folder_fails(run_mstack, tmp_path: Path):
    completed = run_mstack("skills-check", str(tmp_path / "nowhere"))

    assert completed.returncode == 1
    assert "[folder] is not a folder" in completed.stderr


def test_single_skill_folder_is_checked(run_mstack, skills_sandbox: Path):
    completed = run_mstack("skills-check", str(skills_sandbox / "sync-rules"), "--json")

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["skills"] == ["sync-rules"]
