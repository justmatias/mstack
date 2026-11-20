# Settings

`settings/claude.json` is a partial Claude Code `settings.json`: only the keys mstack manages, such as `permissions`, `statusLine`, `env` and, later, `hooks`.

```json
{
  "permissions": { "allow": ["Bash(mstack:*)"] }
}
```

`setup-mstack` deep-merges it into `~/.claude/settings.json`:

- objects merge by key, arrays such as `permissions.allow` become unions, and mstack's values win only for the keys it ships;
- keys mstack does not define are never touched, so the user's own and per-machine settings stay;
- the plan lists every key it would add or change before anything is written.

The same content rules as `mcp/` apply: `${VAR}` placeholders instead of secrets, no machine-specific paths. Cursor has no equivalent file, so these settings are Claude Code only.

No settings are shipped yet.
