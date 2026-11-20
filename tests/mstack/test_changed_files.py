from pathlib import Path

import pytest

from mstack.changed_files import ChangedFilesError, changed_files
from tests.mstack.conftest import git


def names(paths: list[Path], repository: Path) -> list[str]:
    return [path.relative_to(repository).as_posix() for path in paths]


def test_lists_committed_uncommitted_and_untracked_files(feature_repository, commit):
    (feature_repository / "a.py").write_text("x = 2\n", encoding="utf-8")
    commit(feature_repository)
    (feature_repository / "b.py").write_text("x = 3\n", encoding="utf-8")
    (feature_repository / "new.py").write_text("y = 1\n", encoding="utf-8")

    changed = changed_files(feature_repository, default_base_ref="main")

    assert names(changed, feature_repository) == ["a.py", "b.py", "new.py"]


def test_deleted_files_are_left_out(feature_repository, commit):
    (feature_repository / "b.py").unlink()
    commit(feature_repository)

    assert changed_files(feature_repository, default_base_ref="main") == []


def test_renamed_files_appear_under_their_new_name(feature_repository, commit):
    git(feature_repository, "mv", "a.py", "renamed.py")
    commit(feature_repository)

    changed = changed_files(feature_repository, default_base_ref="main")

    assert names(changed, feature_repository) == ["renamed.py"]


def test_staged_lists_only_the_staged_files(feature_repository):
    (feature_repository / "a.py").write_text("x = 2\n", encoding="utf-8")
    (feature_repository / "b.py").write_text("x = 3\n", encoding="utf-8")
    git(feature_repository, "add", "a.py")

    changed = changed_files(feature_repository, staged=True)

    assert names(changed, feature_repository) == ["a.py"]


def test_missing_explicit_base_ref_fails(feature_repository):
    with pytest.raises(ChangedFilesError, match="does not exist"):
        changed_files(feature_repository, base_ref="origin/missing")


def test_default_base_ref_falls_back_to_the_local_branch(feature_repository, commit):
    (feature_repository / "a.py").write_text("x = 2\n", encoding="utf-8")
    commit(feature_repository)

    changed = changed_files(feature_repository, default_base_ref="origin/main")

    assert names(changed, feature_repository) == ["a.py"]


def test_filters_by_extension(feature_repository, commit):
    (feature_repository / "a.py").write_text("x = 2\n", encoding="utf-8")
    (feature_repository / "notes.txt").write_text("changed\n", encoding="utf-8")
    commit(feature_repository)

    python_only = changed_files(
        feature_repository, default_base_ref="main", extensions=[".py"]
    )
    text_only = changed_files(
        feature_repository, default_base_ref="main", extensions=[".txt"]
    )

    assert names(python_only, feature_repository) == ["a.py"]
    assert names(text_only, feature_repository) == ["notes.txt"]
