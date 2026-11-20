# `mstack install` and `mstack update`

- **Phase:** future
- **Depends on:** `install-manifest` (states, rule rendering, records), `agent-config-folders` (the merge helpers). Better with `skill-validation` and `doctor`.

## Problem

Setup is a skill: an agent reads `setup-mstack/SKILL.md` and does the work with `ls`, `diff`, `cp` and `mv`. That needs an agent session, costs tokens, and can vary between runs and models. Setting up a new machine should be one deterministic command.

## Goal

`mstack install` does what `setup-mstack` does, in Python, with the same safety rules. The skill becomes a thin wrapper for the parts that need judgment.

## Out of scope

- Installing without a checkout (`packaged-install`).
- Profiles (`host-profiles`).

## Design

```text
mstack install [--tool claude|cursor|both] [--only KIND ...] [--dry-run] [--yes] [--json]
mstack update  [--tool ...]   # git pull --ff-only in the source checkout, then install
```

- **Same flow as the skill:** inventory (manifest states for skills, rules, agents, MCP servers, instructions and settings), a plan table, a confirmation, backups to `.mstack-backups/<timestamp>/`, apply, record in the manifest, then run `doctor`.
- **Automatic actions:** `new` → add, `identical` → nothing, `upstream-changed` → update with a backup, old symlink → replace with a copy, duplicate across Claude Code and Cursor folders → remove with a backup.
- **Interactive actions** (or skipped with `--yes`, and listed at the end): `unknown`, `conflict` and `removed` offer keep / update / show diff. "Combine" is not offered: it needs judgment, so the CLI prints "run the `setup-mstack` skill to combine `<name>`".
- **Similar-skill detection** (`known-overlaps.json`, and comparing names and descriptions) stays in the skill.
- **Cursor rules:** printed as today, or written to a file to paste.
- `update` refuses if the checkout has uncommitted changes or is not on its default branch, unless `--force` is passed.

## Changes

- `src/mstack/install/` (`plan.py`, `apply.py`, CLI wiring), reusing manifest, hashing, merge and platform modules.
- `skills/setup-mstack/SKILL.md`: step 1 runs `mstack install --dry-run --json` and presents its plan; the skill handles only overlaps, combines and Cursor rules; then it runs `mstack install` with the approved choices.
- `README.md`, "Getting started" step 2: `mstack install` first, the skill when there are conflicts to combine.

## Tests

- End to end in a temporary `HOME`: a clean install, a second run with nothing to do, an upstream change updated with a backup, a local edit kept, `--dry-run` writes nothing, `--yes` skips the interactive items, `update` with a dirty checkout refuses.

## Acceptance criteria

- [ ] A new machine is set up with `uv tool install --editable <checkout> && mstack install`.
- [ ] The result matches what the skill produces (same files, same manifest).
- [ ] Nothing is written without confirmation, unless `--yes` is passed.
