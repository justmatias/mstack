---
name: setup-mstack
description: "Install or update mstack on this machine for Claude Code, Cursor or Codex: the CLI, skills, rules, subagents, MCP servers, global instructions and settings. Compares each item with what is already installed, shows one plan, and asks only where the user's own setup differs. Use for /setup-mstack ($setup-mstack in Codex), set up mstack, install mstack, update mstack, or after pulling a new version of the mstack repo."
disable-model-invocation: true
---

# Set up mstack

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any combined skill or rule. (2) **Practices, not domain**: a combined skill or rule keeps coding practices only, never business names, rules, values, URLs or verbatim code taken from the user's version. Details: `skills/sync/references/principles.md` in this checkout.

This skill runs from the mstack checkout (`<mstack>`, the folder with `skills/` and `rules/`), and is never installed. It lives in `.agents/skills/`, which Codex, Cursor and opencode load as project skills; Claude Code reaches it through `CLAUDE.md`, which imports `AGENTS.md`. Installing and updating are the same run: the user pulls the repo and runs it again.

You decide how to do the work, with ordinary file tools and the shell the machine has (PowerShell on native Windows). This page says what a finished setup looks like, what to watch out for, and the rules you never break.

## Done means

1. `mstack --help` works from any folder, and `mstack --version` matches `<mstack>/pyproject.toml`.
2. Every tool the user picked loads the mstack skills, rules and agents. If Cursor also loads a copy needed by another selected tool, doctor reports the duplicate.
3. Every MCP server, setting and global instruction mstack ships is configured, without losing a key or a line of the user's.
4. Nothing of the user's was lost: everything replaced is in a backup, and every difference from their own setup was their decision.
5. `mstack doctor` reports no errors (step 5).

## The rules you never break

- **Ask before you write.** Show one plan (step 3), and change nothing until the user approves it.
- **Back up before you replace or remove.** Move the old item into `<the folder it came from>/.mstack-backups/<UTC timestamp>/`, with the timestamp as `YYYYMMDD-HHMMSS` so `mstack cleanup` can prune it, for example `~/.claude/skills/.mstack-backups/20261120-101500/sync/`. A rule is the exception: Claude Code and Cursor load every file under a rules folder, however deep, so back it up beside that folder, into `<the rules folder's parent>/.mstack-backups/<UTC timestamp>/rules/`, for example `~/.claude/.mstack-backups/20261120-101500/rules/naming.md`. Never as `<name>.bak` next to it: the tools would load the backup too. For a shared file (`settings.json`, `mcp.json`, `CLAUDE.md`), back up the whole file first.
- **Never overwrite the user's own edits silently.** When an installed item differs from mstack's version, find out which side changed and ask (step 4).
- **Never write a secret.** `${VAR}` placeholders in `mcp/` and `settings/` stay as they are; the user sets the variables on each machine.
- **Never edit `~/.claude.json` or Cursor's settings database by hand.**

## 1. Find out where things go

Ask which tools to configure: **Claude Code, Cursor, Codex, or any combination?** Run `uv run mstack platform` in `<mstack>` and show the relevant folders. Use the paths it prints, including `CODEX_HOME` when set in the shell that runs Codex.

| Item | Claude Code | Cursor | Codex |
| --- | --- | --- | --- |
| Skills (`skills/<group>/<name>/`, installed flat as `<name>/`) | `~/.claude/skills/` | `~/.cursor/skills/`, subject to sharing below | `~/.agents/skills/` in the home where Codex runs |
| Agents (`agents/<name>.md`) | `~/.claude/agents/` | `~/.cursor/agents/`, subject to sharing below | `<codex>/agents/<name>.toml` |
| Rules (`rules/<name>.mdc`) | `~/.claude/rules/<name>.md` | pasted into Cursor Settings → Rules → User Rules | a managed block in `<codex>/AGENTS.md` |
| Global instructions (`instructions/global.md`) | a `<!-- mstack:begin -->` … `<!-- mstack:end -->` block in `~/.claude/CLAUDE.md` | pasted with the rules | included in the rules block |
| MCP servers (`mcp/<name>.json`) | `claude mcp add-json --scope user <name> '<json>'` | `mcpServers.<name>` in `~/.cursor/mcp.json` | `mcp_servers.<name>` in `<codex>/config.toml` |
| Settings (`settings/claude.json`, `settings/cursor.json`, `settings/codex.json`) | deep-merged into `~/.claude/settings.json` | deep-merged into `~/.cursor/hooks.json` | deep-merged into `<codex>/hooks.json` |

- **Skill sharing:** Install in `~/.claude/skills/` when Claude Code is selected and in `~/.agents/skills/` when Codex is selected. If Cursor shares the home with either, it uses those skills. If all three share the home, Cursor can see both required copies. Install a separate Cursor copy when it shares the home with neither, including when it runs on Windows and the other tools run in WSL.
- **Agent sharing:** Cursor can share Claude Code's agents if they run in the same home. Codex agents use TOML with `name` and `description` from the Markdown frontmatter and `developer_instructions` from its body. Preserve any upstream credit in TOML comments.
- **Codex instructions:** Use a non-empty `<codex>/AGENTS.override.md` if present, since Codex gives it precedence. Run `uv run mstack render-rule --combined <mstack>` for the full block. Replace one existing block or append it after the user's text, leaving the surrounding content intact. If the markers are malformed or duplicated, show the proposed repair for approval before editing.
- **Codex hooks:** If inline `[hooks]` already exists in `<codex>/config.toml`, merge the entries there to keep one hook source for that layer. Ask the user to review and trust the installed hooks in Codex.
- **Codex MCP:** Keep the user's other TOML entries. For a local server use `command`, `args` and `env` for literal values. Forward environment variables by name using `env_vars` when the variable keeps its name, or an explicit user-approved launcher when it needs remapping. For an HTTP server use `url`. Check the result with `codex mcp list`.

The optional asset formats and install destinations are documented in `docs/setup/agent-assets.md`. Empty asset folders are skipped.

**WSL:** Claude Code inside WSL uses the WSL home, and Cursor on Windows reads the Windows profile (`/mnt/c/Users/<user>/.cursor`). If `mstack platform` cannot find it, ask the user for it and export `MSTACK_WINDOWS_HOME=/mnt/c/Users/<user>` for every `mstack` command.

## 2. Compare what is there

For every item, compare mstack's version with the installed one (`diff -ru` for skill folders, `diff -u` for files; ignore `.DS_Store`, `__pycache__` and `.mstack-backups`). Rules are compared in their installed form: `uv run mstack render-rule <mstack>/rules/<name>.mdc` prints it (no frontmatter, an `Applies to` line from `globs`, no `## Checks`, the upstream credit at the end). Always install that output rather than converting by hand, so `mstack doctor` can tell later whether the copy drifted.

Sort each item into one of these, and work out the rest yourself:

- **Missing**: install it.
- **Same**: nothing to do.
- **Different**: find out which side changed. `git -C <mstack> log -p -- <path>` shows mstack's history for the item: if the installed copy equals an older mstack version, only mstack moved on, so update it (with a backup) without asking. Otherwise the user edited it, or it is someone else's item under the same name: ask (step 4).
- **Old setup leftovers**: a symlink into an mstack checkout (replace it with a copy), a skill renamed since (`integrate-skills` → `integrate`, `reflect-rules` → `reflect`, `correct-rules` → `correct`, `sync-rules` → `sync`, `review` → `diff-review`), or an extra skill copy in a compatibility folder. Before proposing removal, verify that the old copy matches mstack's history and each selected tool can find the replacement.
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

1. **The CLIs first**, since the skills run `mstack <command>` and `rulepack <command>`, and the agent hooks run `rulepack hook`. If `mstack --version` does not match this checkout, tell the user and run `uv tool install --editable <mstack> --reinstall`. Then install rulepack at the tag in `[tool.mstack] rulepack` of `<mstack>/pyproject.toml`, unless `rulepack --version` already reports it: `uv tool install --force git+https://github.com/justmatias/rulepack@<tag>`. It brings `ast-grep` and `import-linter`. If `uv` is missing, give the user the install command for their system from <https://docs.astral.sh/uv/>.
2. Apply what was approved, backing up first. For settings and MCP config files, merge mstack's keys into the existing document using its JSON or TOML format. Merge objects by key and lists by union. For instructions, replace the text between the markers, or append the block if there is none. When updating an existing Claude Code MCP registration, run `claude mcp remove --scope user <name>` first.
3. **Cursor rules**: print the approved rules and the global instructions as one block of plain text (each rule's `description` as a heading, then its rendered text), and tell the user to paste it into Cursor Settings → Rules → User Rules.
4. Run `mstack doctor --tool` with the selected names separated by commas, for example `mstack doctor --tool claude,codex`. Fix every error and run it again. Mention any warnings, including drift on an item the user chose to keep. For the selected tools, also verify the resulting MCP registrations, settings and agents. Check that `~/.claude/CLAUDE.md` has one mstack block when installing Claude Code global instructions.

## 6. Reply

A short list. Leave out empty lines:

- Added / updated / combined / replaced / kept: the items, by kind.
- Removed: leftovers and duplicates.
- Keys written in `settings.json`, `hooks.json`, `mcp.json` or `config.toml`.
- Environment variables to set on this machine (every `${VAR}` an installed item uses).
- Cursor rules: printed for pasting, or skipped.
- Backups: `<folder>/.mstack-backups/<timestamp>/`, and for rules `<the rules folder's parent>/.mstack-backups/<timestamp>/rules/`.
- Open a new session in the tools you configured. Later, `mstack doctor` shows drift, and `/repair` (`$repair` in Codex) fixes it.
