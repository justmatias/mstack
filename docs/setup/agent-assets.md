# Optional agent assets

`setup-mstack` installs files from these optional folders in the checkout. Each asset is a separate file, and folder README files are not installed.

## Agents

Put one Markdown file per agent in `agents/<name>.md`. Include frontmatter with `name` matching the filename and a `description` that tells the main agent when to use it. Optional Claude Code fields include `tools` and `model`.

The setup skill installs agents for Claude Code or Cursor. Cursor can use Claude Code's agents when both tools share a home. Codex agents use TOML and are converted during setup.

## Global instructions

Put shared project guidance in `instructions/global.md`, in plain Markdown. Keep it short, in English, and free of domain details and machine-specific paths.

Setup adds it as a managed block to Claude Code's `~/.claude/CLAUDE.md`, prints it for Cursor User Rules, and includes it in the Codex instructions block.

## MCP servers

Put one JSON object per server in `mcp/<name>.json`, using the `mcpServers` entry format without the server name around it:

```json
{
  "command": "npx",
  "args": ["-y", "<package>@<version>"],
  "env": { "SERVICE_TOKEN": "${SERVICE_TOKEN}" }
}
```

Remote servers use `"type": "http"` and `"url"` instead of `command`. Use `${VAR}` placeholders for secrets. Never store tokens, keys, passwords, or machine-specific paths in these files.

Setup registers servers with Claude Code, merges them into Cursor's `mcp.json`, or merges them into Codex's `config.toml`.

## Editor settings

Put a partial settings object in `settings/claude.json`, containing only the keys mstack manages. Put Cursor hook entries in `settings/cursor.json`. Setup deep-merges the fragments into `~/.claude/settings.json` or `~/.cursor/hooks.json`, merging objects by key and arrays by union. User settings outside mstack's keys remain intact. Use `${VAR}` for secrets and avoid machine-specific paths.
