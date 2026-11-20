# Install manifest

- **Phase:** now
- **Depends on:** none. Used by `doctor`, `rollback-and-uninstall`, `install-command` and `version-pinning`.

## Problem

`setup-mstack` compares each skill and rule with what is installed, but, in its own words, "there is no manifest, so a `differs` skill may be the user's own edit or a newer mstack version". On every update the user reviews diffs that are only upstream changes, and a local edit on one laptop looks the same as an outdated copy on the other.

## Goal

Record what mstack installed and its content hash, so each item gets a precise state. Upstream-only changes update safely, and only real conflicts reach the user.

## Out of scope

- Doing the install itself in Python (`install-command`). This spec adds the commands the `setup-mstack` skill calls.

## Design

**Location:** `${XDG_STATE_HOME:-~/.local/state}/mstack/manifest.json` (on Windows `%LOCALAPPDATA%\mstack\manifest.json`). It is machine state, not configuration, and it is never committed.

```json
{
  "schema": 1,
  "items": [
    {
      "kind": "skill",
      "name": "sync-rules",
      "target": "~/.claude/skills/sync-rules",
      "hash": "sha256:...",
      "source_version": "3.0.0",
      "source_commit": "<40-char sha or null>",
      "installed_at": "2026-11-20T10:15:00Z"
    }
  ]
}
```

- **Hash:** sha256 over the sorted relative paths and contents of every file, ignoring `.DS_Store` and `__pycache__` (the same ignore list as the skill). For a rule, hash the converted `.md` text.
- **Rule conversion in Python:** move the `.mdc` → `~/.claude/rules/<name>.md` conversion from `setup-mstack` step 3 into `src/mstack/install/rules.py`, so the hash is reproducible. The skill calls `mstack render-rule <file.mdc>` instead of converting by hand.
- **States**, from the source hash S, the recorded hash R and the installed hash I:

| Condition | State | Default action |
| --- | --- | --- |
| No record, nothing installed | `new` | add |
| No record, I = S | `identical` | record it |
| No record, I ≠ S | `unknown` | ask (today's `differs`) |
| I = R, S = R | `identical` | none |
| I = R, S ≠ R | `upstream-changed` | update (back up first) |
| I ≠ R, S = R | `locally-edited` | keep, and tell the user |
| I ≠ R, S ≠ R | `conflict` | ask: update, keep or combine |
| Record, nothing installed | `removed` | ask: reinstall or forget |
| Record, no longer in the source | `orphan` | ask: uninstall (see `rollback-and-uninstall`) or keep |

**Commands:**

- `mstack manifest status --tool claude|cursor|both [--json]`: computes the state of every skill and rule in the checkout against its target.
- `mstack manifest record <kind> <name> <target>`: records the current hash after the skill installs an item.
- `mstack manifest forget <kind> <name>`.
- `mstack render-rule <file.mdc>`: prints the converted rule.

Writes are atomic (write to a temporary file, then rename). An unknown `schema` fails with a clear message.

## Changes

- Add `src/mstack/install/` with `hashing.py`, `rules.py`, `manifest.py`, and register the commands in `cli.py`.
- `skills/setup-mstack/SKILL.md`: steps 2 and 3 use `mstack manifest status --json` for the states. Step 4 shows the new states. Step 5 asks only about `unknown`, `conflict` and `removed`, and reports `locally-edited` items. Step 6 runs `mstack manifest record` after each install and writes rules with `mstack render-rule`. Remove the "there is no manifest" paragraph.

## Tests

- Hash stability: file order, ignored files, and a change in one byte changes the hash.
- `render-rule`: frontmatter dropped, the `Applies to` line from `globs`, `## Checks` dropped, the body kept. Compare against the current skill's rules for every file in `rules/`.
- Every row of the state table, in a temporary `HOME` and state directory.
- Atomic write and unknown-schema handling.

## Docs

- `src/mstack/README.md`: the commands.
- `README.md`, step 4 "Update": updates only ask about real conflicts.

## Acceptance criteria

- [ ] A second `setup-mstack` run right after the first shows everything `identical` and asks nothing.
- [ ] Changing a skill in the checkout yields `upstream-changed`; editing the installed copy yields `locally-edited`; both yield `conflict`.
- [ ] The manifest lives outside every tool folder and outside the repo.

## Open questions

- Record items installed before this spec? Recommendation: the first run records every `identical` item automatically and leaves `unknown` items for the user.
