from pathlib import Path

import pytest

from mstack.guards.check_commit_msg import clean_message, suggestion


@pytest.fixture
def commit_message(git_repository: Path, run_mstack):
    """Run mstack commit-msg on a message, inside a repo with its own config."""

    def check(message: str):
        path = git_repository / "COMMIT_EDITMSG"
        path.write_text(message, encoding="utf-8")
        return run_mstack("commit-msg", str(path), working_directory=git_repository)

    return check


@pytest.mark.parametrize(
    "message",
    [
        "feat: add the shell rules\n",
        "fix(lint): skip the scan when nothing changed\n",
        "refactor(install)!: drop the old manifest schema\n",
        "docs: explain the hooks\n\nThe README only listed the ids, not when each runs.\n",
        "feat: " + "a" * 66 + "\n",
    ],
    ids=["plain", "scope", "breaking", "body", "72-characters"],
)
def test_valid_message_passes(commit_message, message: str):
    completed = commit_message(message)

    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("feature: add the rules\n", "'feature' is not an allowed type"),
        ("Feat: add the rules\n", "Conventional Commits subject"),
        ("feat:add the rules\n", "Conventional Commits subject"),
        ("feat: " + "a" * 67 + "\n", "73 characters, at most 72"),
        ("feat: add the rules.\n", "no trailing period"),
        ("feat: add the rules\nBecause they were missing.\n", "blank line"),
    ],
    ids=[
        "unknown-type",
        "uppercase-type",
        "missing-space",
        "73-characters",
        "trailing-period",
        "no-blank-line",
    ],
)
def test_invalid_message_fails_with_the_rule_and_an_example(
    commit_message, message: str, expected: str
):
    completed = commit_message(message)

    assert completed.returncode == 1
    assert expected in completed.stderr
    assert "rules/git-commits.mdc" in completed.stderr
    assert "Example: feat: a" in completed.stderr


@pytest.mark.parametrize(
    "message",
    [
        "Merge branch 'main' into feature\n",
        'Revert "feat: add the rules"\n\nThis reverts commit abc.\n',
        "fixup! feat: add the rules\n",
        "squash! feat: add the rules\n",
    ],
    ids=["merge", "revert", "fixup", "squash"],
)
def test_generated_messages_pass(commit_message, message: str):
    assert commit_message(message).returncode == 0


def test_comments_and_scissors_are_ignored(commit_message):
    message = (
        "feat: add the rules\n"
        "# Please enter the commit message for your changes.\n"
        "# ------------------------ >8 ------------------------\n"
        "diff --git a/x b/x\n"
        "+Some line that would break the rules.\n"
    )

    assert commit_message(message).returncode == 0


def test_empty_message_fails(commit_message):
    completed = commit_message("# only a comment\n")

    assert completed.returncode == 1
    assert "empty" in completed.stderr


def test_custom_types_from_the_config(commit_message, write_config):
    write_config('[commits]\ntypes = ["change", "fix"]\n')

    assert commit_message("change: rename the module\n").returncode == 0
    assert commit_message("feat: add the rules\n").returncode == 1


def test_clean_message_keeps_the_body_and_drops_trailing_blank_lines():
    assert clean_message("feat: x\n\nWhy.\n\n# comment\n\n") == "feat: x\n\nWhy."


def test_suggestion_fixes_type_scope_and_period():
    assert suggestion("Feat(My Scope): add it.", ["feat", "fix"]) == (
        "feat(my-scope): add it"
    )


def test_suggestion_for_a_long_subject_fits_the_limit():
    example = suggestion("feat: " + "word " * 30, ["feat"])

    assert len(example) <= 72
    assert example.startswith("feat: word")
