---
name: setup-mstack
description: "Install or update the mstack skills (skills/), rules (rules/), subagents (agents/), MCP servers (mcp/), global instructions (instructions/) and settings (settings/) into your user-level Claude Code and Cursor setup, asking you what to add, update, replace or discard for each one. Use when the user says set up mstack, install mstack, update mstack skills, update mstack rules, or after pulling a new version of the mstack repo."
---

# Set up mstack

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any combined skill or rule. (2) **Practices, not domain**: a combined skill or rule keeps coding practices only, never business names, rules, values, URLs or verbatim repo code taken from the user's version. Details: [principles.md](../sync-rules/references/principles.md).

Install the mstack skills, rules, agents, MCP servers, global instructions and settings from this checkout into the user-level setup that Claude Code and Cursor load. Run it with the mstack repo open: `<mstack>` below is that checkout's root (the folder with `skills/` and `rules/`). Updating is the same flow: pull the repo, then run this skill again.

You do the work with ordinary file tools (`ls`, `diff -ru`, `cp -R`, `mkdir -p`, `mv`) and the `mstack` CLI from this checkout (`uv run mstack ...` inside `<mstack>`). Nothing is written until the user approves it. Never overwrite or delete anything without a backup.

mstack keeps a manifest of what it installed and the content hash of each item, outside every tool folder and outside the repo (`${XDG_STATE_HOME:-~/.local/state}/mstack/manifest.json`, or `%LOCALAPPDATA%\mstack\manifest.json` on Windows). It is how this skill tells a user's own edit from a newer mstack version.

## 1. Ask which tools the user uses

Ask this first, before reading anything else: **Claude Code, Cursor, or both?** Then state in one or two lines where things will go:

| Tools | Skills and agents go to | Rules go to | MCP servers | Instructions | Settings |
| --- | --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/`, `~/.claude/agents/` | `~/.claude/rules/` | `claude mcp add-json --scope user` | managed block in `~/.claude/CLAUDE.md` | merged into `~/.claude/settings.json` |
| Cursor | `~/.cursor/skills/`, `~/.cursor/agents/` | Cursor Settings → Rules (pasted by the user, see step 8) | merged into `~/.cursor/mcp.json` | printed for Cursor Settings → Rules | none |
| Both | `~/.claude/skills/` and `~/.claude/agents/` only, because Cursor also loads those folders and a second copy would show every item twice | `~/.claude/rules/`, plus Cursor Settings → Rules | both of the above | both of the above | merged into `~/.claude/settings.json` |

**Where each tool's files are.** Run `mstack platform` from `<mstack>` and say which home each tool uses before planning anything; the `~/.claude` and `~/.cursor` paths in this skill mean the folders it prints:

- Linux, macOS and native Windows: both tools use the user's home (`%USERPROFILE%` on Windows).
- **WSL**: Claude Code inside WSL uses the WSL home, but Cursor runs on Windows and reads the Windows profile (`/mnt/c/Users/<user>/.cursor`), not `~/.cursor` inside WSL. `mstack platform` finds it through `cmd.exe` and `wslpath`; if it can't, ask the user for the path and export `MSTACK_WINDOWS_HOME=/mnt/c/Users/<user>` for every `mstack` command. Because the tools are in different homes, **Both** means two copies on WSL: skills and agents go to `~/.claude/` and to the Windows `.cursor/`. `mstack manifest status` already plans it that way.

The skills target is called `<skills>` below (two targets on WSL with both tools).

On native Windows, the shell commands in this skill are examples: use the PowerShell equivalents (`Copy-Item -Recurse` for `cp -R`, `Move-Item` for `mv`, `New-Item -ItemType Directory -Force` for `mkdir -p`, `Compare-Object` or `git diff --no-index` for `diff`).

## 2. Inventory the skills

Run `mstack manifest status --tool <claude|cursor|both> --json` from `<mstack>`. It covers every folder in `<mstack>/skills/` that has a `SKILL.md`, **except `setup-mstack`** (this skill only runs from the checkout and is never installed), every rule (step 3), and the agents, MCP servers, instructions and settings (step 4). Each item has a `kind`, `name`, `target`, `state`, `action` and `recorded`. The states:

| State | Meaning | Proposed action |
| --- | --- | --- |
| `new` | Nothing installed and no record | add |
| `identical` | Installed matches what was recorded and the source has not changed (or, with no record, the installed copy equals the source: `action` is `record it`) | none (or record it) |
| `upstream-changed` | Only the mstack version changed since the install | update, backing up first |
| `locally-edited` | Only the installed copy changed: the user's own edit | keep, and tell the user |
| `conflict` | Both changed | ask (step 6): update, keep or combine |
| `unknown` | No record, and the installed copy differs from the source | ask (step 6) |
| `removed` | Recorded, but nothing is installed any more | ask: reinstall or forget |
| `orphan` | Recorded, but no longer in the checkout | ask: uninstall (back up first) or keep |
| `old-symlink` | A symlink into an mstack checkout (left by the old setup) | replace with a copy |

Check one more state yourself: `duplicate`, with both tools, a copy or symlink of the same mstack skill in `~/.cursor/skills/` → discard the duplicate. To see what changed for `upstream-changed`, `conflict` or `unknown`, `diff -ru <mstack>/skills/<name> <skills>/<name>` (ignore `.DS_Store` and `__pycache__`).

Then look for **similar skills**: any other skill in the folders the selected tools load (`~/.claude/skills/`, and `~/.cursor/skills/` with Cursor) that does the same job under another name. Start from [known-overlaps.json](references/known-overlaps.json) (pstack `reflect` ↔ `reflect-rules`, pstack `correct` ↔ `correct-rules`), then compare names and descriptions. For each candidate, read both `SKILL.md` files and keep it only if they really overlap. Say in one line why.

## 3. Inventory the rules (Claude Code)

Skip this step if the user does not use Claude Code.

Sources: every `<mstack>/rules/*.mdc`. Each one installs as `~/.claude/rules/<name>.md`, and `mstack render-rule <mstack>/rules/<name>.mdc` prints the converted text. Never convert by hand: the manifest hashes the rendered text, so it must be reproducible. The conversion:

1. Drop the `.mdc` frontmatter (`description`, `globs`, `alwaysApply`). Claude Code only reads `paths:` from a rule, and `paths:` in user-level rules is unreliable, so the rule is installed without it and always loads.
2. If the rule had `globs`, start the body with one line: `Applies to files matching <globs>.`
3. Drop the `## Checks` section: those checks only run inside the mstack repo.
4. Keep the rest of the body as it is.

The rule states come from the same `mstack manifest status` output as the skills (`kind: rule`). To see what changed, `diff -u <(mstack render-rule <mstack>/rules/<name>.mdc) ~/.claude/rules/<name>.md`. Also look for **similar rules** in `~/.claude/rules/` (same topic under another file name) by reading them, and keep only real overlaps.

## 4. Inventory agents, MCP servers, instructions and settings

The same `mstack manifest status --json` output covers them, with the same states. Each folder's `README.md` describes its format and is never installed.

| Kind | Source | What mstack owns at the target | See what changes |
| --- | --- | --- | --- |
| `agent` | `<mstack>/agents/<name>.md` | the whole file | `diff -u` against the installed file |
| `mcp` | `<mstack>/mcp/<name>.json` | `mcpServers.<name>` in `~/.claude.json` (Claude Code) or `~/.cursor/mcp.json` (Cursor); one row per target | `mstack merge-settings <mstack>/mcp/<name>.json <target> --under mcpServers --under <name> --dry-run` |
| `instructions` | `<mstack>/instructions/global.md` | the `<!-- mstack:begin -->` … `<!-- mstack:end -->` block of `~/.claude/CLAUDE.md` | `mstack merge-block <mstack>/instructions/global.md ~/.claude/CLAUDE.md --dry-run`, then compare the block |
| `settings` | `<mstack>/settings/claude.json` | the keys the fragment defines in `~/.claude/settings.json` | `mstack merge-settings <mstack>/settings/claude.json ~/.claude/settings.json --dry-run` |

For the merged kinds (`mcp`, `instructions`, `settings`), the state only looks at what mstack owns: the user's other keys and the text outside the block never make an item `locally-edited`. `locally-edited` means the user changed or removed a value mstack wrote. The dry runs print every key they would add, change or extend (`changes`): put those keys in the plan, because the user must see every key mstack changes.

Also look for **similar agents** in the folders the selected tools load (`~/.claude/agents/`, and `~/.cursor/agents/` with Cursor), and for an MCP server already configured under another name for the same tool, the same way as for skills.

## 5. Show the plan and wait

Show one table, one row per item: name, kind (skill, rule, agent, mcp, instructions or settings), purpose (one line, in your own words, from its `description` and body: what it does and when it is used), state, proposed action, and "similar to `<name>`" for confirmed overlaps. Wait for the user's approval. Do not ask about rows whose action is obvious (`new` → add, `identical` → nothing or record it, `upstream-changed` → update with a backup, `old-symlink` → replace with a copy). List `locally-edited` rows so the user knows their edits are kept. For `mcp` and `settings` rows, list under the row every key the dry run would change, with the old and new value for a `change`.

## 6. Ask about every conflict

For each `unknown`, `conflict`, `removed` and `orphan` item, each confirmed similar item, and anything the user wants to change in the table, ask the user to pick one option. Do not ask about the other states. "Theirs" is mstack's version, "mine" is the installed one:

| Choice | Effect |
| --- | --- |
| **Add** | Install mstack's version. For a similar item with a different name, both stay installed. |
| **Update** | Back up the installed version, then install mstack's version over it. |
| **Replace** | For a similar item: back up the user's item and remove it, then install mstack's version. |
| **Discard** | Do not install mstack's version, and leave what is installed untouched. For a `duplicate`, back it up and remove it. |
| **Forget** | For a `removed` item: drop its record with `mstack manifest forget <kind> <name>`. |
| **Combine** | Draft one merged item (see below) and install it after approval. |

Ask about one item at a time, and give the user what they need to decide without opening any file:

1. **Purpose.** In two or three lines, say what the mstack version does and when it is used. For an `unknown` or `conflict` item, also say what the installed version does. For a similar item, say what the user's skill or rule does and where the two overlap or differ in purpose.
2. **What changed.** Summarize the differences in plain words (for example "adds a `--check` mode", "drops the reviewer templates", "only the wording of step 3 changed"), and which side changed: for a `conflict`, both did (the user edited it and mstack has a newer version).
3. **The diff** (`diff -ru` for a skill, `diff -u` for a rule or an agent, the dry-run `changes` for `mcp` and `settings`, the old and new block for `instructions`). For a long diff, show the parts that matter and offer the rest.
4. **Your recommendation** and one line of why, then the question.

**Combine:**

1. Draft the merged item in a temp folder outside the repo and outside every tool folder. Start from mstack's version and bring over what only the user's version has.
2. A merged skill keeps the frontmatter `name` equal to its folder name. If either side had the principles header (`> **Principles (always apply):** ...`), the merged skill keeps it at the top. If either side credits pstack (`license` and `metadata.adapted-from` in the frontmatter, or an `Adapted from pstack/<skill> (MIT)` line), the merged skill keeps that credit in its frontmatter.
3. Relative links into `../sync-rules/references/` must still resolve: every mstack skill is installed side by side in `<skills>`.
4. Show the diff of the draft against both versions, and install it only after the user explicitly approves it.

## 7. Apply what was approved

- **Back up first.** Move whatever you are about to overwrite or remove into `<folder>/.mstack-backups/<UTC timestamp>/<name>`, inside the folder it came from (for example `~/.claude/skills/.mstack-backups/20261120-101500/sync-rules/`). Never put backups next to the skills or rules as `<name>.bak` or similar: the tools would load them.
- A symlink is removed with `rm` (its target is the checkout; nothing to back up).
- Copy skills with `cp -R <mstack>/skills/<name> <skills>/<name>`, then delete any `.DS_Store` or `__pycache__` that came along.
- Write each rule with `mstack render-rule <mstack>/rules/<name>.mdc > ~/.claude/rules/<name>.md`.
- Copy each agent with `cp <mstack>/agents/<name>.md <agents folder>/<name>.md`.
- **Merged items: back up the whole target file first** (copy it into `<its folder>/.mstack-backups/<UTC timestamp>/`, for example `~/.claude/.mstack-backups/20261120-101500/settings.json`), then:
  - settings: `mstack merge-settings <mstack>/settings/claude.json ~/.claude/settings.json --write`;
  - instructions: `mstack merge-block <mstack>/instructions/global.md ~/.claude/CLAUDE.md --write`;
  - an MCP server for Claude Code: `claude mcp add-json --scope user <name> "$(cat <mstack>/mcp/<name>.json)"`. If it already exists, `claude mcp remove --scope user <name>` first (it was backed up with `~/.claude.json`). Never edit `~/.claude.json` by hand;
  - an MCP server for Cursor: `mstack merge-settings <mstack>/mcp/<name>.json ~/.cursor/mcp.json --under mcpServers --under <name> --write`.
  Never write a secret: `${VAR}` placeholders stay as they are, and the user sets the variables on each machine.
- **Record every item you installed, updated or combined**, and every `identical` item whose `action` is `record it`: `mstack manifest record <kind> <name> <target>` from `<mstack>`. For a combined item, record it after installing the merged version. For `mcp` and `settings`, the record also stores the keys mstack wrote. The `<target>` is the file the item went into (`~/.claude.json`, `~/.cursor/mcp.json`, `~/.claude/settings.json`, `~/.claude/CLAUDE.md`), as `manifest status` shows it. For an uninstalled `orphan`, run `mstack manifest forget <kind> <name>` after backing it up and removing it.
- Install the `mstack` CLI, which the installed skills call to run the guards (see `../sync-rules/references/authoring-a-check.md`). If `mstack --help` already works, leave it. Otherwise ask the user, then run `uv tool install --editable <mstack>`.

## 8. Cursor rules and instructions

Skip this step if the user does not use Cursor. Cursor has no file-based user rules folder (it does not load `~/.cursor/rules/`), and its user rules live in Cursor Settings → Rules. So:

1. Ask the user which mstack rules they want in Cursor (default: the ones they approved for Claude Code, or all of them).
2. Print them as one block of plain text, ready to paste: for each rule, its `description` as a heading, the `Applies to ...` line, and the body without frontmatter or `## Checks`.
3. If `<mstack>/instructions/global.md` exists, add it to the same block under a "Global instructions" heading.
4. Tell the user to paste it into **Cursor Settings → Rules → User Rules**. Do not edit Cursor's settings database.

## 9. Verify

Run `mstack doctor --tool <tools>` (`uv run mstack doctor` inside `<mstack>` if the CLI is not on `PATH` yet). It checks the tools, that the `mstack` on `PATH` is this version, the checkout, that every skill is installed and passes `skills-check --profile generic` with no duplicate between `~/.claude/skills/` and `~/.cursor/skills/`, that every rule is in `~/.claude/rules/` without frontmatter, and the manifest states. Fix every error it reports and run it again; mention its warnings to the user. Then check by hand what doctor does not:

- Every installed agent has a frontmatter `name` equal to its file name, and no mstack agent exists in both `~/.claude/agents/` and `~/.cursor/agents/` when the user picked both.
- `claude mcp list` shows the MCP servers installed for Claude Code, and `~/.cursor/mcp.json` is still valid JSON.
- `~/.claude/settings.json` is still valid JSON and still has the user's own keys, and `~/.claude/CLAUDE.md` has one mstack block.

Tell the user everything shows up in a new session of Claude Code or Cursor, and name every `${VAR}` an installed MCP server or setting needs set on this machine.

## 10. Reply

A short list. Leave out empty lines:

- Skills added / updated / replaced / combined / discarded: ...
- Rules added / updated / replaced / combined / discarded: ...
- Agents, MCP servers, instructions and settings added / updated / combined / discarded: ... (for settings and MCP servers, the keys written)
- Environment variables to set: ...
- Duplicates removed and old symlinks replaced: ...
- Cursor rules: printed for pasting (or skipped).
- Backups: `<folder>/.mstack-backups/<timestamp>/`
