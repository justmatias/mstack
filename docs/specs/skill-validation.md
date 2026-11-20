# Skill validation

- **Phase:** now
- **Depends on:** none. `doctor` reuses the validator for installed skills.

## Problem

`setup-mstack` step 8 checks by hand that each installed skill has a `SKILL.md` whose `name` matches its folder, that it has a `description`, and that `../sync-rules/references/` resolves. Nothing checks this in the repo, so a renamed folder, a broken relative link or a missing principles header only shows up on a machine after install.

## Goal

`mstack skills-check` validates every skill in a folder, and CI runs it on `skills/`.

## Out of scope

- Judging how well a skill is written, or tuning its description.
- Validating `agents/` and the other new folders (`agent-config-folders` extends the command).

## Design

```text
mstack skills-check [DIR ...] [--profile mstack|generic] [--json]
```

`DIR` defaults to `skills/` (or the configured folder). Each folder with a `SKILL.md` is one skill.

| Check | Profile | Error when |
| --- | --- | --- |
| `frontmatter` | both | missing, not YAML, or not a mapping |
| `name` | both | missing, not kebab-case, or not equal to the folder name |
| `description` | both | missing, empty, or longer than 1024 characters |
| `links` | both | a relative Markdown link (`[x](path)`) points to a missing file. Links into a sibling skill resolve from the installed layout, where skills sit side by side |
| `unused-files` | both | a file under `references/` or `scripts/` is linked from nowhere (warning) |
| `principles` | mstack | the first block after the title is not the `> **Principles (always apply):**` header |
| `credit` | mstack | `license` without `metadata.adapted-from`, or the reverse; `adapted-from` without an `upstream-commit` that is a 40-character sha |
| `english` | mstack | non-ASCII letters outside code spans and quoted examples (warning, since names may need them) |

The `generic` profile is for skills that aren't mstack's (for example `doctor` over `~/.claude/skills/`). It also accepts optional frontmatter keys such as `disable-model-invocation`, and unknown keys only warn.

## Changes

- Add `src/mstack/guards/check_skills.py` and register `skills-check` in `cli.py`.
- Add the step to the `make guards` flow, or to `mstack lint` when `runtime-lint-command` has landed (step `skills`, run when `skills/` exists).
- Fix whatever the first run finds in `skills/`.

## Tests

- `tests/mstack/guards/test_check_skills.py`: a sandbox copy of `skills/` passes. Then one test per check: rename a folder, empty a description, break a link, drop the principles header, remove `upstream-commit`, add an unlinked reference.
- The `generic` profile ignores the mstack-only checks.

## Docs

- `src/mstack/README.md`: the command and its checks.
- `skills/setup-mstack/SKILL.md` step 8: run `mstack skills-check <skills> --profile generic` instead of checking by hand.
- `skills/integrate-skills/SKILL.md`: run it on the integrated skill before proposing it.

## Acceptance criteria

- [ ] `mstack skills-check` passes on `skills/` and runs in CI through `make lint-rules`.
- [ ] Each check has a failing test.
- [ ] `setup-mstack` and `integrate-skills` use it.
