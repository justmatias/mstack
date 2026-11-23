# Claude Code plugin

- **Phase:** future
- **Depends on:** nothing open. Packages `skills/` and `agents/`, validated by `mstack skills-check`. The plugin can ship the Claude Code hooks from `settings/claude.json`.

## Problem

Claude Code has a native way to distribute skills, subagents, hooks and MCP servers: plugins from a marketplace, installed and updated by Claude Code itself. mstack copies files into `~/.claude/` instead. Updating a machine means `git pull`, running `setup-mstack` again, and `mstack doctor` with `/repair` to catch drift. On a machine that only uses Claude Code, the plugin would make updates automatic.

## Goal

The repo is also a Claude Code marketplace with one `mstack` plugin. On a Claude Code-only machine, adding the marketplace and installing the plugin gives the same skills and agents as the copied install, and Claude Code handles updates.

## Out of scope

- Rules, global instructions and settings: plugins don't install user rules or merge `settings.json`, so `setup-mstack` still handles those.
- Machines that also use Cursor. Cursor loads `~/.claude/skills/`, not Claude Code plugins, so those machines need the copied skills anyway, and Claude Code would then list each skill twice (`mstack:sync` and `sync`). They keep the copy-based install.

## Design

- Add `.claude-plugin/marketplace.json` (the marketplace, listing one plugin) and `.claude-plugin/plugin.json` (name, description, version, author, license). Check the current plugin docs for the exact schema; `claude plugin validate` must pass.
- **Layout:** the checkout groups skills as `skills/<group>/<name>/`, while every install, and `skills-check`'s link resolution, treat them as flat `<name>/` folders. The plugin must see the flat layout, so links between skills (`../sync/references/`) keep working. Two options, to choose at implementation time:
  1. `plugin.json` lists each skill folder explicitly, if the schema allows custom skill paths and links still resolve between siblings.
  2. A release step builds the plugin into a generated folder with the flat layout, and the marketplace points at it (a release branch or a release asset).
- Plugin components: every skill except `setup-mstack` (it lives in `.agents/skills/` and is never installed), `agents/`, and the Claude Code hooks from `settings/claude.json` as `hooks/hooks.json`.
- Plugin skills are namespaced (`mstack:sync`). Update skill text that refers to other skills by bare name only where it matters.
- **Version:** semantic-release writes the version into `plugin.json` too (`version_variables` or a JSON updater in `[tool.semantic_release]`).
- **No double install:** a machine uses either the plugin or copied skills. `setup-mstack` asks which one when the user picks Claude Code only, and skips copying skills and agents when the plugin is installed. `doctor` flags copied mstack skills next to the plugin.

## Changes

- `.claude-plugin/`, the layout step chosen above, and the semantic-release config.
- A CI step running `claude plugin validate` (or a schema check when the CLI isn't available in CI).
- `README.md`, "Getting started": a Claude Code-only alternative with the two commands.
- `setup-mstack` and `doctor`: plugin detection.

## Tests

- Schema validation in CI. `plugin.json` version equals `pyproject.toml` version.
- Every skill in `skills/<group>/` except `setup-mstack` is in the plugin, under its flat name, and its relative links resolve there.

## Docs

- `README.md`: the install alternative, and that machines with Cursor keep the copied install.
- `.agents/skills/setup-mstack/SKILL.md`: the plugin-or-copy choice.

## Acceptance criteria

- [ ] On a clean Claude Code-only machine, adding the marketplace and installing the plugin makes every mstack skill and agent available.
- [ ] A release updates the plugin version.
- [ ] Copied skills and the plugin never coexist without doctor flagging it.

## Open questions

- Whether `plugin.json` supports custom skill paths, which decides between the two layout options.
