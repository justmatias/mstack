# Rules enforced by pre-commit hooks

- **Phase:** now (prerequisite of `rule-pack-shell` and `rule-pack-git-commits`)
- **Depends on:** none

## Problem

`mstack coverage` only accepts `enforced-by: <id>` when `<id>` is an ast-grep rule or an import-linter contract. Some rules are best enforced by an existing linter run as a pre-commit hook: shellcheck for shell quoting, gitleaks for committed secrets, `no-commit-to-branch` for direct commits to `main`, a commit-message check. Today such a rule would be reported as `unknown-check`, or would have to be marked `llm-review` even though a tool enforces it.

## Goal

A rule's `## Checks` section can name a pre-commit hook, and `mstack coverage` verifies the hook is configured.

## Out of scope

- Reverse coverage for hooks: hooks have no `metadata.source`, and many hooks (formatters, mypy) don't belong to a prose rule. Only rule → hook is checked.
- CI-only checks that are not pre-commit hooks.

## Design

New line in the `## Checks` section:

```markdown
## Checks
- enforced-by-hook: shellcheck
```

- A separate keyword (not `enforced-by:`) makes the kind explicit. It also keeps ids from colliding (an ast-grep rule and a hook with the same id), and keeps `unlisted-check` logic unchanged.
- `mstack coverage` reads `.pre-commit-config.yaml` (path from `.mstack.toml`, key `pre_commit_config`, default `.pre-commit-config.yaml`) and collects every `hooks[].id` from every repo, including `local` ones.
- New issue kind `unknown-hook`: the hook id is not in the config. A missing config file makes every `enforced-by-hook` an `unknown-hook`.
- A hook listed but disabled through `SKIP` is still configured; that is a CI concern, not coverage.
- `--json` adds `hooks` to each rule entry.

## Changes

- `src/mstack/guards/check_rule_coverage.py`: parse `enforced-by-hook`, load hook ids, report `unknown-hook`. A section with only `enforced-by-hook` lines counts as having checks (no `missing-checks-section`).
- `src/mstack/config.py` (if `project-config` has landed): the `pre_commit_config` key. Otherwise a `--pre-commit-config` flag.
- `skills/sync-rules/references/rule-format.md`: the new line in the Checks table, and when to use it.
- `skills/sync-rules/references/authoring-a-check.md`, step 1: a new row, "an existing linter run as a pre-commit hook" (shellcheck, gitleaks, a commit-message check), tried after ast-grep and import-linter. Note that the hook must be pinned (`hookpin` already checks pins in this repo).
- `sync-rules` step 4: `unknown-hook` in the drift list.

## Tests

- `tests/mstack/guards/test_check_rule_coverage.py`: a rule listing a configured remote hook passes; a `local` hook passes; an unknown hook reports `unknown-hook`; a missing config file; a section with only hook lines is not `missing-checks-section`.

## Acceptance criteria

- [ ] `enforced-by-hook` works in this repo against `.pre-commit-config.yaml`.
- [ ] The rule-format and authoring references document it.
- [ ] Existing rules and tests are unaffected.
