---
name: setup-mstack
description: "Install or update the mstack skills (sync-rules, reflect-rules, correct-rules) in your user-level skill folder for Claude Code and Cursor, by copy, with a manifest, backups and a decision for every conflict. Use when the user says set up mstack, install mstack, update mstack skills, /setup-mstack, or after pulling a new version of the mstack repo."
---

# Set up mstack

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any merged skill. (2) **Practices, not domain**: a merged skill keeps coding practices only, never business names, rules, values, URLs or verbatim repo code taken from the other skill. Details: [principles.md](../../../skills/sync-rules/references/principles.md).

Install the mstack skills from this repo's `skills/` folder into the one user skill folder your tools load, by copying them. Run it from the mstack repo. Updating is the same flow: pull the repo, then run this skill again.

The deterministic work is done by `scripts/setup.py skills` (plan, apply, verify). You make the judgment calls: whether a similar skill really overlaps, which version to keep, and how to combine two skills. Never write into the skill folders yourself. Every change goes through `apply`.

All commands run from the mstack repo root:

```bash
uv run python scripts/setup.py skills plan --tools <tools> --json > <scratch>/plan.json
uv run python scripts/setup.py skills apply --plan <scratch>/plan.json --decisions <scratch>/decisions.json --dry-run
uv run python scripts/setup.py skills verify --tools <tools> --json
```

`<scratch>` is a temp folder outside the repo and outside every skill folder.

## 1. Ask which tools the user uses

Ask: Claude Code, Cursor, or both. Then explain the target in one line:

| Tools | `--tools` | Target |
| --- | --- | --- |
| Claude Code only | `claude` | `~/.claude/skills/` |
| Cursor only | `cursor` | `~/.cursor/skills/` |
| Both | `claude,cursor` | `~/.claude/skills/` only, because Cursor also loads that folder. A second copy in `~/.cursor/skills/` would show every skill twice. |

## 2. Plan

Run `plan --json` and read every item. Each item has an `id` (the key for its decision), `skill`, `action`, `path`, `source_hash`, `installed_hash`, `manifest_hash` and `similar_to`.

| `action` | Meaning | Proposed decision |
| --- | --- | --- |
| `install` | Not present in the target | `install` |
| `update` | Pristine mstack copy, the source changed | `update` |
| `unchanged` | Already up to date | none (no decision needed) |
| `modified-locally` | The installed copy differs from what mstack installed (or the manifest is missing or corrupt) | ask (step 5) |
| `collision` | Same name, not installed by mstack | ask (step 5) |
| `migrate-symlink` | An old symlink into an mstack checkout, from the previous setup | `install` (replaces it with a copy) |
| `duplicate` | An mstack copy or link that the tools would load in addition to the target | `remove-duplicate` (step 6) |

If `manifest` is `corrupt`, say so: nothing present is overwritten without the user's decision.

## 3. Check the similar skills

`similar_to` lists candidates only: name-token overlap, description word overlap, and the [known overlaps](references/known-overlaps.json) (pstack `reflect` and `correct`). For each candidate, read both `SKILL.md` files and decide whether they really do the same job. Drop the false positives, and say in one line why each confirmed one overlaps.

## 4. Show the plan and wait

Show one table, one row per item: `id` → `action` → proposed decision (plus "similar to `<name>`" for confirmed overlaps). Wait for the user's approval before going on. Do not ask about rows whose decision follows from the table in step 2.

## 5. Conflicts: keep mine, keep theirs, keep both, or combine

For every `collision`, every `modified-locally` item and every confirmed similar skill, ask the user to pick one option. "Mine" is the user's installed skill, "theirs" is mstack's:

| Choice | Decision | Effect |
| --- | --- | --- |
| Keep mine | `keep-mine` | Leaves the installed folder as it is. The manifest records it as kept. You are asked again only when the mstack source changes. |
| Keep theirs | `keep-theirs` | Backs up the installed folder, then installs mstack's copy. |
| Keep both | `keep-both` | Leaves the installed folder in place and installs mstack's copy as `mstack-<name>`, with its frontmatter `name` rewritten. |
| Combine | `merged:<path>` | Installs a merged skill folder that you drafted and the user approved. |

For a confirmed similar skill with a different name (for example pstack `reflect` next to `reflect-rules`), nothing collides on disk. The plan item is still `install` or `update`. "Keep mine" there means `skip`. "Keep both" is the plain `install`. "Combine" is a `merged:<path>` on the mstack item, and afterwards the user can delete their own skill by hand.

**Combine:**

1. Draft the merged folder in `<scratch>/merged/<installed name>/`. Start from mstack's copy (`skills/<skill>/` in this repo), and bring over what only the other side has. Keep the frontmatter `name` equal to the folder name the item installs to (`installed_as` in the plan).
2. If either side had the principles header (`> **Principles (always apply):** ...`), the merged skill keeps it at the top. If either side had the pstack attribution line (`Adapted from pstack/<skill> (MIT). ...`), the merged skill keeps it as its last line.
3. Relative links into `../sync-rules/references/` must still resolve. The merged folder lands next to `sync-rules` in the target.
4. Show `diff -ru` of the merged folder against both versions (the installed one at `path`, and mstack's in `skills/<skill>/`).
5. Pass `merged:<scratch>/merged/<installed name>` only after the user explicitly approves the diff.

## 6. Duplicates

For every `duplicate`, propose `remove-duplicate`. For example, with both tools selected, an mstack copy in `~/.cursor/skills/` would make Cursor load the skill twice. Old project-level symlinks in this repo's `.claude/skills/` or `.cursor/skills/` show up here too. Removal backs the folder up first (a symlink is just unlinked).

## 7. Old symlinks

For every `migrate-symlink`, the decision is `install`: the symlink is removed and a copy is installed in its place.

## 8. Apply

Write the decisions as one JSON object keyed by item `id` (items with action `unchanged` need no entry):

```json
{"sync-rules": "install", "reflect-rules": "merged:/tmp/x/merged/reflect-rules", "correct-rules@~/.cursor/skills": "remove-duplicate"}
```

Run `apply` with `--dry-run` first and check that the output matches the approved table. Then run it again without `--dry-run`. If `apply` reports that the plan is stale, something changed on disk: go back to step 2.

`apply` backs up everything it replaces or removes into `<folder>/.mstack-backups/<timestamp>/<skill>/`, never as sibling folders (the tools would load those as skills). It writes `<target>/.mstack-manifest.json` and the toolkit config `~/.config/mstack/config.json`, which the installed skills use to find this repo's `scripts/`.

## 9. Verify

Run `verify --json` and fix or report every problem. It checks:

- the frontmatter of every installed skill (its `name` matches the folder, and it has a `description`);
- that `../sync-rules/references/` resolves from every installed skill, since they must land side by side;
- that the toolkit config is readable and points at a folder with `scripts/`.

Tell the user that the skills show up in a new session of Claude Code or Cursor.

## 10. Reply

Reply with a short list built from `apply --json`. Leave out empty lines:

- Installed: ...
- Updated: ...
- Skipped: ...
- Merged: ...
- Removed duplicates: ...
- Kept (edited): ...
- Kept both: ...
- Backups: `<folder>/.mstack-backups/<timestamp>/`
