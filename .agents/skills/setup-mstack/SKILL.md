---
name: setup-mstack
description: "Install or update mstack on this machine: the mstack CLI, the skills (skills/), rules (rules/), subagents (agents/), MCP servers (mcp/), global instructions (instructions/) and settings (settings/), into the user-level folders Claude Code and Cursor load. Compares each item with what is already installed, shows one plan, and asks only where the user's own setup differs. Use for /setup-mstack ($setup-mstack in Codex), set up mstack, install mstack, update mstack, or after pulling a new version of the mstack repo."
disable-model-invocation: true
---

# Set up mstack

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any combined skill or rule. (2) **Practices, not domain**: a combined skill or rule keeps coding practices only, never business names, rules, values, URLs or verbatim code taken from the user's version. Details: `skills/sync/references/principles.md` in this checkout.

This skill runs from the mstack checkout (`<mstack>`, the folder with `skills/` and `rules/`), and is never installed. It lives in `.agents/skills/`, which Codex, Cursor and opencode load as project skills; Claude Code reaches it through `CLAUDE.md`, which imports `AGENTS.md`. Installing and updating are the same run: the user pulls the repo and runs it again.

You decide how to do the work, with ordinary file tools and the shell the machine has (PowerShell on native Windows). This page says what a finished setup looks like, what to watch out for, and the rules you never break.

## Done means

1. `mstack --help` works from any folder, and `mstack --version` matches `<mstack>/pyproject.toml`.
2. Every tool the user picked loads every mstack skill, rule and agent, exactly once.
3. Every MCP server, setting and global instruction mstack ships is configured, without losing a key or a line of the user's.
4. Nothing of the user's was lost: everything replaced is in a backup, and every difference from their own setup was their decision.
5. `mstack doctor` reports no errors (step 5).

## The rules you never break

- **Ask before you write.** Show one plan (step 3), and change nothing until the user approves it.
- **Back up before you replace or remove.** Move the old item into `<the folder it came from>/.mstack-backups/<UTC timestamp>/`, for example `~/.claude/skills/.mstack-backups/20261120-101500/sync/`. Never as `<name>.bak` next to it: the tools would load the backup too. For a shared file (`settings.json`, `mcp.json`, `CLAUDE.md`), back up the whole file first.
- **Never overwrite the user's own edits silently.** When an installed item differs from mstack's version, find out which side changed and ask (step 4).
- **Never write a secret.** `${VAR}` placeholders in `mcp/` and `settings/` stay as they are; the user sets the variables on each machine.
- **Never edit `~/.claude.json` or Cursor's settings database by hand.**

## 1. Find out where things go

Ask first: **Claude Code, Cursor, or both?** Then run `uv run mstack platform` in `<mstack>` and say where each tool's user folder is. Everything below that says `~/.claude` or `~/.cursor` means the folders it prints.

| Item | Claude Code | Cursor | Both |
| --- | --- | --- | --- |
| Skills (`skills/<group>/<name>/`, installed flat as `<name>/`: the group is never part of the installed path), agents (`agents/<name>.md`) | `~/.claude/skills/`, `~/.claude/agents/` | `~/.cursor/skills/`, `~/.cursor/agents/` | `~/.claude/` only: Cursor loads it too, and a second copy shows every item twice. On WSL, a copy in each home |
| Rules (`rules/<name>.mdc`) | `~/.claude/rules/<name>.md` | pasted into Cursor Settings → Rules → User Rules | both |
| Global instructions (`instructions/global.md`) | a `<!-- mstack:begin -->` … `<!-- mstack:end -->` block in `~/.claude/CLAUDE.md` | pasted with the rules | both |
| MCP servers (`mcp/<name>.json`) | `claude mcp add-json --scope user <name> '<json>'` | `mcpServers.<name>` in `~/.cursor/mcp.json` | both |
| Settings (`settings/claude.json`) | deep-merged into `~/.claude/settings.json` | none | Claude Code's |

Each folder's `README.md` explains its format and is never installed. Today `agents/`, `mcp/`, `instructions/` and `settings/` may hold nothing else: then skip them.

**WSL:** Claude Code inside WSL uses the WSL home, and Cursor on Windows reads the Windows profile (`/mnt/c/Users/<user>/.cursor`). If `mstack platform` cannot find it, ask the user for it and export `MSTACK_WINDOWS_HOME=/mnt/c/Users/<user>` for every `mstack` command.

## 2. Compare what is there

For every item, compare mstack's version with the installed one (`diff -ru` for skill folders, `diff -u` for files; ignore `.DS_Store`, `__pycache__` and `.mstack-backups`). Rules are compared in their installed form: `uv run mstack render-rule <mstack>/rules/<name>.mdc` prints it (no frontmatter, an `Applies to` line from `globs`, no `## Checks`, the upstream credit at the end). Always install that output rather than converting by hand, so `mstack doctor` can tell later whether the copy drifted.

Sort each item into one of these, and work out the rest yourself:

- **Missing**: install it.
- **Same**: nothing to do.
- **Different**: find out which side changed. `git -C <mstack> log -p -- <path>` shows mstack's history for the item: if the installed copy equals an older mstack version, only mstack moved on, so update it (with a backup) without asking. Otherwise the user edited it, or it is someone else's item under the same name: ask (step 4).
- **Old setup leftovers**: a symlink into an mstack checkout (replace it with a copy), a skill renamed since (`integrate-skills` → `integrate`, `reflect-rules` → `reflect`, `correct-rules` → `correct`, `sync-rules` → `sync`: offer to remove the old one), or a copy in `~/.cursor/skills/` that `~/.claude/skills/` already has when both tools share the home (remove it).
- **Similar**: another skill, rule, agent or MCP server already installed that does the same job under another name. [known-overlaps.json](references/known-overlaps.json) lists the ones mstack knows about (an upstream that an mstack skill was adapted from); otherwise compare names and descriptions, read both, and keep only real overlaps. An overlap under the same name shows up as **Different**: recommend **Combine** for it.

For a merged item (MCP server, settings, instructions), only what mstack ships counts: the user's other keys and the text outside the mstack block are theirs and never make the item different. List every key you would add or change, with the old and new value.

## 3. Show the plan and wait

One table, one row per item that needs something: name, kind, one line on what it does (from its description, in your own words), what you found, and what you will do. Mention in one line how many items are already the same. Mark the rows that need an answer, and wait for the user's approval.

## 4. Ask about each difference

For each **Different** or **Similar** item, and each leftover you would remove, ask one at a time, so the user can decide without opening a file:

1. What mstack's version does, and what the installed one does.
2. What differs, in plain words ("adds a `--check` mode", "only the wording of step 3"), and which side changed.
3. The parts of the diff that matter (offer the rest).
4. Your recommendation and one line of why.

The choices: **keep** theirs, **update** to mstack's (back up first), **replace** a similar item with mstack's (back up and remove theirs), **add** mstack's next to a similar one, or **combine**. To combine, draft the merged item in the scratchpad or a temp folder, outside the repo and every tool folder: start from mstack's version, bring over what only theirs has, keep the skill's `name` equal to its folder, keep the principles header and any upstream credit (`license`, `metadata.adapted-from`), and keep relative links into `../sync/references/` working. Show the diff against both versions and install it only after approval.

## 5. Apply and check

1. **The CLI first**, since the skills run it as `mstack <command>`. If `mstack --version` does not match this checkout, tell the user and run `uv tool install --editable <mstack> --reinstall` (it brings `ast-grep` too). If `uv` is missing, give the user the install command for their system from <https://docs.astral.sh/uv/>.
2. Apply what was approved, backing up first. For a merged item, read the target, merge mstack's keys in (objects by key, lists as unions, mstack's values win only for the keys it ships), and write valid JSON back; for instructions, replace the text between the markers, or append the block if there is none. For an MCP server already configured in Claude Code, `claude mcp remove --scope user <name>` first.
3. **Cursor rules**: print the approved rules and the global instructions as one block of plain text (each rule's `description` as a heading, then its rendered text), and tell the user to paste it into Cursor Settings → Rules → User Rules.
4. Run `mstack doctor --tool <claude|cursor|both>`. Fix every error and run it again; mention the warnings. A `drift` warning on an item the user chose to keep is expected: say so. Also check what doctor does not: `claude mcp list` shows the servers, `~/.claude/settings.json` and `~/.cursor/mcp.json` are valid JSON with the user's keys still there, and `~/.claude/CLAUDE.md` has one mstack block.

## 6. Reply

A short list. Leave out empty lines:

- Added / updated / combined / replaced / kept: the items, by kind.
- Removed: leftovers and duplicates.
- Keys written in `settings.json` and `mcp.json`.
- Environment variables to set on this machine (every `${VAR}` an installed item uses).
- Cursor rules: printed for pasting, or skipped.
- Backups: `<folder>/.mstack-backups/<timestamp>/`.
- Open a new Claude Code or Cursor session to load everything. Later, `mstack doctor` shows drift, and `/repair` fixes it.
