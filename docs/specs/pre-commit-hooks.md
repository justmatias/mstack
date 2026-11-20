# Pre-commit hooks for other repos

- **Phase:** now
- **Depends on:** `runtime-lint-command` (the hooks run `mstack lint`, which must bring its own ast-grep).

## Problem

This repo runs its checks through a `local` hook (`make lint-rules-changed STAGED=1`). A work repo can't reuse it: it would need the Makefile, `uv`, and ast-grep in its own dev dependencies.

## Goal

Any repo adds mstack to `.pre-commit-config.yaml` with a pinned `rev`, and pre-commit installs and runs it in its own environment.

## Out of scope

- The commit-message hook's logic (`rule-pack-git-commits` adds `mstack commit-msg`; this spec only reserves its entry).
- Changing this repo's own `local` hook.

## Design

Add `.pre-commit-hooks.yaml` at the repo root:

| id | entry | stage | pass_filenames | Notes |
| --- | --- | --- | --- | --- |
| `mstack-lint` | `mstack lint --files` | pre-commit | yes | ast-grep scan of the staged files with `--error` |
| `mstack-rules` | `mstack lint --only test coverage` | pre-commit | no | `files` limited to rule, check and test paths |
| `mstack-exceptions` | `mstack exceptions` | pre-commit | yes | |
| `mstack-leak-check` | `mstack leak-check` | pre-commit | no | uses `[leak_check]` from `.mstack.toml` |
| `mstack-imports` | `mstack lint --only imports` | pre-commit | no | runs when `.importlinter` or Python files change |
| `mstack-commit-msg` | `mstack commit-msg` | commit-msg | yes | added by `rule-pack-git-commits` |

- `language: python`: pre-commit installs the package at `rev`, with `ast-grep-cli` and `import-linter` as runtime dependencies.
- `mstack-imports` warns in its description that import-linter needs the project importable, and that `additional_dependencies` may be needed.
- A sample config block goes in the README, pinned to a full tag (`rev: v3.1.0`).

## Changes

- Add `.pre-commit-hooks.yaml`.
- `mstack lint --files`: confirm it accepts the filenames pre-commit passes and filters them by `[scan].extensions` (done in `runtime-lint-command`; test it here).
- `.pre-commit-config.yaml`'s `check-yaml` covers the new file automatically.

## Tests

- `tests/test_pre_commit_hooks.py`: parse `.pre-commit-hooks.yaml`; every `entry` command exists in `mstack --help`; every id is unique.
- An integration test, marked `slow` and run in CI: in a temporary repo with a bad Python file, `pre-commit try-repo <checkout> mstack-lint --all-files` fails, and passes once the file is fixed.

## Docs

- `README.md`: a "Use the checks in another repo" section with the pre-commit snippet.
- `init-command` templates use these ids.

## Acceptance criteria

- [ ] `pre-commit try-repo` works for every hook from a clean environment.
- [ ] No hook needs anything installed in the target repo besides pre-commit.
