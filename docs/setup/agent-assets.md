# Agent assets

`setup-mstack` installs files from these folders in the checkout. Each asset is a separate file, and folder README files are not installed.

## Agents

Put one Markdown file per agent in `agents/<name>.md`. Include frontmatter with `name` matching the filename and a `description` that tells the main agent when to use it. Optional Claude Code fields include `tools` and `model`.

The setup skill installs agents for Claude Code or Cursor. Cursor can use Claude Code's agents when both tools share a home. Codex agents use TOML and are converted during setup.

## Editor settings

Put a partial settings object in `settings/claude.json`, containing only the keys mstack manages. Put Cursor hook entries in `settings/cursor.json` and Codex hook entries in `settings/codex.json`. Setup deep-merges the fragments into `~/.claude/settings.json`, `~/.cursor/hooks.json` or `$CODEX_HOME/hooks.json`, merging objects by key and arrays by union. User settings outside mstack's keys remain intact. Use `${VAR}` for secrets and avoid machine-specific paths.
