# MCP servers

One MCP server per file: `mcp/<name>.json`, in the `mcpServers` entry format, without the server name around it.

```json
{
  "command": "npx",
  "args": ["-y", "<package>@<version>"],
  "env": { "SERVICE_TOKEN": "${SERVICE_TOKEN}" }
}
```

A remote server uses `"type": "http"` and `"url"` in place of `command`.

- **Claude Code:** `setup-mstack` runs `claude mcp add-json --scope user <name> '<json>'`. It never edits `~/.claude.json` by hand.
- **Cursor:** merged into `~/.cursor/mcp.json` under `mcpServers.<name>`, keeping the user's other servers.

Secrets are never written here. Any value that looks like a token, key or password must be a `${VAR}` placeholder, resolved on each machine. This repo's gitleaks hook scans every commit for secrets; `make repo-guards` also runs `mstack domain-check` over these files, for URLs, hosts and emails. Use `~` or `${HOME}`, never a machine-specific path.

No servers are shipped yet.
