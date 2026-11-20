# Agent config folders

- **Phase:** now
- **Depends on:** `install-manifest` (soft: installed items are recorded when it exists). `agent-hooks` and `per-host-secrets` build on this spec.

## Problem

mstack keeps skills and rules, but the rest of a working agent setup lives only on each machine: subagent definitions, MCP servers, global instructions, settings such as permissions and the status line. Setting up a second laptop means recreating them by hand, and they drift.

## Goal

The repo holds these pieces in versioned folders, and `setup-mstack` installs them with the same inventory → plan → approval → backup flow it uses for skills.

## Out of scope

- Hook content (`agent-hooks`). This spec only makes `settings/` able to carry hooks.
- Resolving secrets (`per-host-secrets`). This spec allows `${VAR}` placeholders and forbids literal values.
- Slash commands: Claude Code serves them from skills now, so there is no `commands/` folder.

## Design

| Folder | Holds | Installs to (Claude Code) | Cursor |
| --- | --- | --- | --- |
| `agents/<name>.md` | Subagent definitions (frontmatter `name`, `description`, optional `tools`, `model`) | `~/.claude/agents/<name>.md` (copy) | Verify support at implementation time; skip if none |
| `mcp/<name>.json` | One MCP server each, in the `mcpServers` entry format | `claude mcp add-json --scope user <name> '<json>'`, never by editing `~/.claude.json` by hand | Merged into `~/.cursor/mcp.json` |
| `instructions/global.md` | Global instructions for every project | A managed block in `~/.claude/CLAUDE.md` | Printed for Cursor Settings → Rules, as rules are today |
| `settings/claude.json` | A partial `settings.json`: `permissions`, `statusLine`, `env`, later `hooks` | Deep-merged into `~/.claude/settings.json` | none |

**Merging, not overwriting**, because these files also hold the user's own and per-machine settings:

- **Managed block:** `<!-- mstack:begin -->` … `<!-- mstack:end -->` in `CLAUDE.md`. Only the text between the markers is replaced; anything outside stays.
- **JSON deep merge:** objects merge by key; arrays of strings (`permissions.allow`) are unions; scalars from mstack win, but the plan shows each key it changes; keys mstack doesn't define are never touched. To remove a key mstack added earlier, use the manifest record, which stores the keys mstack wrote.
- Every write is backed up first to `<folder>/.mstack-backups/<timestamp>/`, like skills.

**Rules for the content** (checked by `skills-check`, extended to these folders):

- `agents/*.md` frontmatter `name` equals the file name, and `description` is present.
- `mcp/*.json` and `settings/*.json` parse, and string values hold no literal secret: anything that looks like a token or key must be a `${VAR}` placeholder. `mstack leak-check` and gitleaks run over the folders.
- Everything follows the principles: English, no domain details, no machine-specific paths (use `~` or `${HOME}`).

## Changes

- Add `agents/`, `mcp/`, `instructions/` and `settings/`, each with a README describing its format. Start them empty or with one example only after the user picks one (see open questions).
- `skills/setup-mstack/SKILL.md`: new steps after rules, "Inventory agents, MCP servers, instructions and settings", reusing the states, the plan table and the backup rules. With `install-manifest`, record each item, and for settings record the keys written.
- Add `src/mstack/install/merge.py` (deep merge and managed block), called by the skill through `mstack merge-settings <fragment> <target> --dry-run|--write` so the merge is deterministic.
- Extend `mstack skills-check` (or add `mstack config-check`) to validate the new folders, and add the step to `mstack lint` / `make lint-rules`.
- `mstack leak-check` paths for this repo include the new folders.

## Tests

- Merge: union of arrays, nested objects, user keys preserved, a dry run writes nothing, and the result is the same when run twice.
- Managed block: inserted when missing, replaced when present, text outside untouched.
- Validation: an agent with a mismatched name, an MCP file with a literal token, invalid JSON.

## Docs

- `README.md`: the "What's inside" table and the install table gain the new folders.
- Each folder's README.

## Acceptance criteria

- [ ] `setup-mstack` installs an agent, an MCP server, the global instructions and a settings fragment on a clean `HOME`, and a second run changes nothing.
- [ ] Existing user settings survive the merge, and the plan shows every key mstack changes.
- [ ] CI fails on a literal secret in `mcp/` or `settings/`.

## Open questions

- Which first items to ship? Candidates: a read-only code-review subagent; the permission allowlist for `mstack`, `uv run`, `git status` and `git diff`; a global instruction telling agents to run `mstack doctor` when `mstack` is missing.
- Cursor support for `agents/` and an API for its user rules: check the current Cursor docs when implementing.
