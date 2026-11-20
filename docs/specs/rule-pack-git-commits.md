# Rule pack: git and commit conventions

- **Phase:** now
- **Depends on:** `hook-checks` (the checks are pre-commit hooks). Reads the allowed types from `.mstack.toml`.

## Problem

Agents commit a lot, and the conventions are only partly enforced. In this repo, `pr-title.yml` checks PR titles and `[tool.semantic_release]` lists the allowed types, but commit messages themselves are not checked. The rest (one change per commit, never commit secrets or local settings, don't commit to `main`) lives only in agent instructions. Work repos have none of it.

## Goal

A `rules/git-commits.mdc` rule, a `mstack commit-msg` guard that any repo can run as a `commit-msg` hook, and hooks for the checkable parts.

## Out of scope

- Branch protection settings on GitHub.
- Rewriting history or squashing policies beyond what a rule can say.

## Design

`rules/git-commits.mdc`, `alwaysApply: true` (it is about the commit, not about files):

| Bullet | Check |
| --- | --- |
| Commit subjects follow Conventional Commits: `type(scope)!: summary`, with a type from the allowed list | `enforced-by-hook: mstack-commit-msg` |
| The subject is at most 72 characters, in the imperative mood, with no trailing period | `mstack-commit-msg` (length and period); the mood is judgment |
| The body, when present, is separated by a blank line and explains why, not what | `mstack-commit-msg` (blank line); content is judgment |
| One logical change per commit | `llm-review` |
| Never commit secrets, keys or local settings files | `enforced-by-hook: gitleaks`, `enforced-by-hook: detect-private-key` |
| Never commit directly to the default branch; branch first | `enforced-by-hook: no-commit-to-branch` |
| Don't force-push shared branches | `llm-review` |

**`mstack commit-msg <file>`:**

- Reads the message file pre-commit passes and drops comment lines (`#`) and anything after the scissors line that git adds with `--verbose`.
- Validates `^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<summary>.+)$`, the type against the allowed list, the subject length, no trailing period, and the blank line before the body.
- Allows the messages git and tools generate: `Merge ...`, `Revert "..."`, `fixup!` and `squash!` (these are rejected on the default branch by CI, not by the hook).
- Allowed types: `.mstack.toml` key `[commits].types`. The default is the list from this repo's `allowed_tags`: build, chore, ci, docs, feat, fix, perf, refactor, style, test.
- Each error names the rule it breaks and shows a corrected example.

## Changes

- `src/mstack/guards/check_commit_msg.py`, registered as `commit-msg` in `cli.py`.
- `.pre-commit-hooks.yaml` (from `pre-commit-hooks`, or created here): the `mstack-commit-msg` hook with `stages: [commit-msg]`.
- This repo's `.pre-commit-config.yaml`: a `local` `mstack-commit-msg` hook (`uv run mstack commit-msg`, `stages: [commit-msg]`), and `no-commit-to-branch` from `pre-commit-hooks` (`args: [--branch, main]`). Set `default_install_hook_types: [pre-commit, commit-msg]` so `pre-commit install` installs both.
- CI: `make lint` already skips the local `lint-rules` hook. Commit-msg hooks don't run on `--all-files`; add a step that runs `mstack commit-msg` on each commit of the PR (`git log --format=%B base..HEAD`, one message at a time).
- `rules/git-commits.mdc`.

## Tests

- `tests/mstack/guards/test_check_commit_msg.py`: valid subjects (with scope, with `!`, with body), and invalid ones (unknown type, uppercase type, missing space, 73-character subject, trailing period, no blank line before the body). Merge and revert messages pass. Comment and scissors lines are ignored. Custom types from `.mstack.toml` are respected.
- `mstack coverage` resolves all four hooks.

## Docs

- `README.md`: `pre-commit install` installs the commit-msg hook too.
- `src/mstack/README.md`: the command.

## Acceptance criteria

- [ ] A bad commit message is rejected locally with a corrected example.
- [ ] CI rejects a PR containing a non-conventional commit.
- [ ] The rule's checks section lists only hooks that exist, and `mstack coverage` passes.

## Open questions

- With squash merges only the PR title reaches `main`, and `pr-title.yml` already checks it. Keep the per-commit CI step anyway? Recommendation: yes. Agents read `git log` on branches too, and the local hook makes it nearly free.
