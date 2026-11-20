# Rollback and uninstall

- **Phase:** next
- **Depends on:** `install-manifest` (knows what mstack installed). Covers the `agent-config-folders` items when that spec has landed.

## Problem

`setup-mstack` backs up everything it replaces to `<folder>/.mstack-backups/<UTC timestamp>/`, but nothing restores from there. There is also no way to remove what mstack installed, for example a rule that was dropped upstream (like `architecture-layers`), or everything when leaving a machine.

## Goal

List backups, restore one, and uninstall mstack-installed items safely.

## Out of scope

- Uninstalling the CLI itself (`uv tool uninstall mstack` is enough; doctor and the README mention it).

## Design

```text
mstack backups list [--json]
mstack backups restore <timestamp> [--item NAME ...] [--dry-run]
mstack backups prune --keep N
mstack uninstall [--kind skill|rule|agent|mcp|settings ...] [NAME ...] [--orphans] [--dry-run]
```

- **list:** scans the `.mstack-backups/` folders of every known target (from the platform folders, and the manifest's targets), and groups entries by timestamp.
- **restore:** before restoring, backs up the current state to a new timestamp, so a restore can be undone. Updates the manifest: a restored item is no longer mstack's version, so it becomes `locally-edited`, or is forgotten if it was never mstack's.
- **uninstall:** removes only items recorded in the manifest, after backing them up. An installed item whose hash differs from the record (`locally-edited`) needs an extra confirmation. `--orphans` selects recorded items that no longer exist in the source checkout (dropped upstream). For settings and instructions, it removes only the keys or managed block mstack wrote.
- Everything prints the plan first, and `--dry-run` stops there.

## Changes

- `src/mstack/install/backups.py`, `src/mstack/install/uninstall.py`, and the CLI registration.
- `skills/setup-mstack/SKILL.md`: when the manifest shows `orphan` items (recorded but gone from the source), propose `mstack uninstall --orphans`. Mention restoring in the reply section.
- `doctor`: warn about orphans, and about backups older than 90 days (suggest `prune`).

## Tests

- In a temporary `HOME`: install, replace, restore, then restore again (undo); uninstall one, `--orphans`, and a locally edited item; prune keeps the newest N; settings uninstall removes only mstack's keys.

## Docs

- `README.md`, "Update": mention restore and uninstall.
- `src/mstack/README.md`: the commands.

## Acceptance criteria

- [ ] Any change `setup-mstack` made can be undone with one command.
- [ ] Uninstall never touches items mstack did not install.
- [ ] A rule dropped upstream is removed on the next setup run, after approval.
