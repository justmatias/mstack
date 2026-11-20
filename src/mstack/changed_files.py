"""The files a change touches, for `mstack lint --changed`.

An explicit base ref (a flag, as in CI) must exist: falling back would silently scan
nothing. Only the configured default falls back to its local branch (`origin/main`
to `main`) when there is no remote.
"""

import subprocess
from pathlib import Path


class ChangedFilesError(Exception):
    pass


def git(root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, text=True, check=False
    )


def git_lines(root: Path, *arguments: str) -> list[str]:
    completed = git(root, *arguments)
    if completed.returncode != 0:
        raise ChangedFilesError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return [line for line in completed.stdout.splitlines() if line]


def ref_exists(root: Path, ref: str) -> bool:
    completed = git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    return completed.returncode == 0


def local_branch(ref: str) -> str:
    """`origin/main` -> `main`; a ref without a remote prefix stays as it is."""
    return ref.split("/", 1)[1] if "/" in ref else ref


def resolve_base_ref(root: Path, explicit: str | None, default: str) -> str | None:
    if explicit is not None:
        if not ref_exists(root, explicit):
            raise ChangedFilesError(
                f"base ref '{explicit}' does not exist. Fetch it first "
                "(CI: actions/checkout with fetch-depth: 0)."
            )
        return explicit
    for candidate in (default, local_branch(default)):
        if ref_exists(root, candidate):
            return candidate
    return None


def committed_changes(root: Path, base_ref: str | None, explicit: bool) -> list[str]:
    if base_ref is None:
        return []
    merge_base = git(root, "merge-base", base_ref, "HEAD")
    if merge_base.returncode != 0:
        if explicit:
            raise ChangedFilesError(
                f"no merge base between '{base_ref}' and HEAD (shallow clone?)."
            )
        return []
    return git_lines(
        root, "diff", "--name-only", "--diff-filter=ACMR", merge_base.stdout.strip()
    )


def changed_files(
    root: Path,
    *,
    base_ref: str | None = None,
    default_base_ref: str = "origin/main",
    staged: bool = False,
    extensions: list[str] | None = None,
) -> list[Path]:
    """Changed files that still exist, as absolute paths, sorted.

    Without `staged`: committed changes since the merge base with the base ref,
    uncommitted changes, and untracked files. With `staged`: only the staged files.
    """
    if staged:
        names = git_lines(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
    else:
        resolved = resolve_base_ref(root, base_ref, default_base_ref)
        names = committed_changes(root, resolved, explicit=base_ref is not None)
        names += git_lines(root, "ls-files", "--others", "--exclude-standard")
    paths = {root / name for name in names}
    return sorted(
        path
        for path in paths
        if path.is_file() and (extensions is None or path.suffix in extensions)
    )
