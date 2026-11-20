# Claude Code plugin

- **Phase:** future
- **Depends on:** `agent-config-folders` (agents and hooks to package), `skill-validation`. Better with `agent-hooks`.

## Problem

Claude Code has a native way to distribute skills, subagents, hooks and MCP servers: plugins from a marketplace, installed and updated by Claude Code itself. mstack copies files into `~/.claude/` instead, so updates depend on re-running setup on each machine.

## Goal

The repo is also a Claude Code marketplace with one `mstack` plugin. On any machine, adding the marketplace and installing the plugin gives the same skills, agents and hooks, and Claude Code handles updates.

## Out of scope

- Rules and settings fragments: plugins don't install user rules or merge `settings.json`, so `mstack install` (or `setup-mstack`) still handles those.
- Cursor (it loads `~/.claude/skills/`, not Claude Code plugins). Cursor users keep the copy-based install.

## Design

- Add `.claude-plugin/marketplace.json` (the marketplace, listing one plugin with `source: "./"`) and `.claude-plugin/plugin.json` (name, description, version, author, license). Check the current plugin docs for the exact schema and folder layout when implementing; `claude plugin validate` must pass.
- Plugin components come from the existing folders: `skills/` (except `setup-mstack`), `agents/`, and `hooks/hooks.json` generated from the hooks in `settings/claude.json`.
- Plugin skills are namespaced (`mstack:sync-rules`). Relative links between skills (`../sync-rules/references/`) keep working because the plugin keeps the same layout. Update skill text that refers to other skills by bare name only where it matters.
- **Version:** semantic-release writes the version into `plugin.json` too (`version_variables` or a JSON updater in `[tool.semantic_release]`).
- **No double install:** a machine uses either the plugin or copied skills. `setup-mstack` and `doctor` detect the installed plugin and skip or flag copied mstack skills.

## Changes

- `.claude-plugin/`, the generated `hooks/hooks.json`, and the semantic-release config.
- A CI step running `claude plugin validate` (or a schema check when the CLI isn't available in CI).
- `README.md`, "Getting started": an alternative step 2, "Claude Code plugin", with the two commands.
- `setup-mstack` and `doctor`: plugin detection.

## Tests

- Schema validation in CI. `plugin.json` version equals `pyproject.toml` version (a test).
- A test that every skill folder is picked up by the plugin layout, except `setup-mstack`.

## Acceptance criteria

- [ ] On a clean machine, adding the marketplace and installing the plugin makes every mstack skill available.
- [ ] A release updates the plugin version.
- [ ] Copied skills and the plugin never coexist without doctor flagging it.
