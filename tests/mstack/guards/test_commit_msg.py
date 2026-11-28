import pytest


def test_commit_msg_passes_when_message_is_valid(
    commit_message, valid_commit_message: str
):
    completed = commit_message(valid_commit_message)

    assert completed.returncode == 0, completed.stderr


def test_commit_msg_fails_with_rule_and_example_when_message_is_invalid(
    commit_message, invalid_commit_message: tuple[str, str]
):
    message, problem = invalid_commit_message

    completed = commit_message(message)

    assert completed.returncode == 1
    assert problem in completed.stderr
    assert "rules/git-commits.mdc" in completed.stderr
    assert "Example: feat: a" in completed.stderr


def test_commit_msg_passes_when_message_is_generated(
    commit_message, generated_commit_message: str
):
    assert commit_message(generated_commit_message).returncode == 0


def test_commit_msg_ignores_lines_when_they_are_comments_or_below_scissors(
    commit_message,
):
    message = (
        "feat: add the rules\n"
        "# Please enter the commit message for your changes.\n"
        "# ------------------------ >8 ------------------------\n"
        "diff --git a/x b/x\n"
        "+Some line that would break the rules.\n"
    )

    assert commit_message(message).returncode == 0


def test_commit_msg_fails_when_message_is_empty(commit_message):
    completed = commit_message("# only a comment\n")

    assert completed.returncode == 1
    assert "empty" in completed.stderr


@pytest.mark.usefixtures("_allow_change_commit_type")
def test_commit_msg_accepts_type_when_mstack_config_lists_it(commit_message):
    assert commit_message("change: rename the module\n").returncode == 0


@pytest.mark.usefixtures("_allow_change_commit_type")
def test_commit_msg_rejects_type_when_mstack_config_omits_it(commit_message):
    assert commit_message("feat: add the rules\n").returncode == 1
