---
name: repair
description: "Close the gaps mstack doctor reports on this machine: run mstack doctor --json, map every error and warning to its fix (reinstall the CLI, install or update drifted skills, rules and agents with a backup, remove duplicate copies, set the WSL Windows home), apply the safe fixes, ask before the ones that touch the user's own edits or software, and rerun doctor until it has no errors. Use for /repair, fix mstack doctor, doctor shows warnings, doctor says ask your agent, or mstack is out of date or broken."
disable-model-invocation: true
---

# Repair

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any combined skill or rule. (2) **Practices, not domain**: a combined skill or rule keeps coding practices only, never business names, rules, values, URLs or verbatim code taken from the user's version. Details: [../sync/references/principles.md](../sync/references/principles.md).

`mstack doctor` only reports. This skill acts on its report: it turns every error and warning into the fix that closes it, applies it, and checks again. It changes only what doctor flagged, never runs the full setup, and never overwrites or deletes anything without a backup.

## 1. Run doctor

1. Run `mstack doctor --json` (add `--tool <claude|cursor|both>` if the user names one, and `--online` if they asked about updates). If `mstack` is not on `PATH`, or it fails to start, the CLI is the first gap: go to the `cli` row in step 2, then run doctor again.
2. Read `checkout`, `tool` and `platform` from the JSON, and keep every result whose `status` is not `ok`. `<mstack>` below is that `checkout`: the setup instructions this skill defers to are in `<mstack>/skills/setup-mstack/SKILL.md`, which is never installed, so read it from there.
3. If nothing is left, say so in one line and stop.

## 2. Map each result to its fix

Group the results by `group` and `check`, and pick the fix from this table. A result doctor adds later and this table lacks: use its `fix` field, or report it to the user.

| Group / check | Fix | Ask first? |
| --- | --- | --- |
| `tools` / `uv`, `git`, `gh` | Install it from the link in `fix`, with the package manager the machine already uses (`brew`, `apt`, `winget`) | Yes: it installs software |
| `cli` / `mstack`, `ast-grep` | `uv tool install --editable <mstack> --reinstall` (it also brings `ast-grep`). If another `mstack` comes first on `PATH`, say which one and where | Yes, once |
| `source` / `checkout` (not found) | The same reinstall, from the checkout the user points you to. Ask where it is | Yes |
| `source` / `checkout` (not a git repository) | Report it; do not run `git init` | No fix |
| `source` / `uncommitted` | The user's work in progress. Report it; never commit, stash or discard it | No fix |
| `skills` / `installed`, `rules` / `installed`, `drift` / any | Step 3, for the named items only | Depends on the state |
| `rules` / `frontmatter` | Back up the rule, then rewrite it with `mstack render-rule <mstack>/rules/<name>.mdc > ~/.claude/rules/<name>.md` and record it (step 3) | No |
| `skills` / `valid` | If the skill is an mstack one, step 3 reinstalls it. If it is the user's own, show the issue and the smallest edit that fixes it | Yes, for the user's own skill |
| `skills` / `duplicates` | Back up each copy in `~/.cursor/skills/` and remove it: Cursor already loads `~/.claude/skills/` | No |
| `platform` / `wsl-cursor` | Ask for the Windows profile (`/mnt/c/Users/<user>`), check that it has a `.cursor` folder, and tell the user to export `MSTACK_WINDOWS_HOME` in their shell profile. Use it for every `mstack` command in this run | Yes |
| `version` / `latest` | If `git -C <mstack> status --porcelain` is empty and the branch tracks `origin`, `git -C <mstack> pull --ff-only`; then reinstall the CLI and run doctor again: the drift rows that appear go through step 3. With uncommitted changes or a branch that is not the default, report it and stop | Yes: it changes the checkout |
| `drift` / `manifest` (error) | Report the error. Never edit the manifest by hand | No fix |

## 3. Bring installed items back in line

Run `mstack manifest status --tool <tool> --json` from `<mstack>` and keep only the items doctor named (a missing skill or rule is `new` or `removed`). The states, and how to install each kind (skills, rules, agents, MCP servers, instructions, settings), are in steps 2 to 4 and 7 of `<mstack>/skills/setup-mstack/SKILL.md`; follow them for these items, without its full inventory.

| State | Action |
| --- | --- |
| `new`, `upstream-changed`, `old-symlink` | Apply without asking: back up, install, record |
| `identical` with `action: record it` | `mstack manifest record <kind> <name> <target>` |
| `removed` | Ask: reinstall or forget |
| `orphan` | Ask: uninstall (back up first) or keep |
| `locally-edited` | Keep the user's edit and say so; this warning stays |
| `conflict`, `unknown` | Ask, with the diff and a recommendation: update, keep or combine (setup-mstack step 6) |

Always:

- **Back up first**, into `<folder>/.mstack-backups/<UTC timestamp>/<name>` inside the folder the item came from, never as `<name>.bak` next to it.
- **Record** every item you install, update or combine with `mstack manifest record <kind> <name> <target>`, or doctor reports it as drift again.
- With Cursor, skills and agents go to `~/.claude/` only when both tools share the home, and to both homes on WSL; `manifest status` already plans the right targets.

## 4. Show the plan and wait

Before changing anything, show one table: each doctor result, the fix you will apply, and whether it needs an answer. Apply the rows that need none after one approval for the batch, and ask the others one at a time with your recommendation and one line of why.

## 5. Apply and check again

Apply the approved fixes in this order: tools, CLI, checkout and version, platform, then installed items (a reinstalled CLI or a pulled checkout changes what drifts). Then run `mstack doctor` again.

- Repeat from step 2 for any new or remaining error. Stop after two rounds that fix nothing, and report what is left and why.
- A warning may stay when it is the user's choice: their uncommitted work, a `locally-edited` item, a declined optional tool. Name each one.

## 6. Reply

A short list. Leave out empty lines:

- Doctor before and after: the error and warning counts.
- Fixed: each result and what closed it (for example "`drift skill sync`: updated, backed up").
- Left on purpose: each remaining warning and why.
- Needs the user: what only they can do (install a tool, export `MSTACK_WINDOWS_HOME`, open a new session so the tools load the new skills).
- Backups: `<folder>/.mstack-backups/<timestamp>/`.
