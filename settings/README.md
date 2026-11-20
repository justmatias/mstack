# Settings

`settings/claude.json` is a partial Claude Code `settings.json`: only the keys mstack manages, such as `permissions`, `statusLine`, `env` and, later, `hooks`.

```json
{
  "permissions": { "allow": ["Bash(mstack:*)"] }
}
```

`setup-mstack` deep-merges it into `~/.claude/settings.json` with `mstack merge-settings settings/claude.json ~/.claude/settings.json --dry-run|--write`:

- objects merge by key, arrays such as `permissions.allow` become unions, and mstack's scalars win;
- keys mstack does not define are never touched, so the user's own and per-machine settings stay;
- the dry run lists every key it would change, and the plan shows them before anything is written;
- the manifest records the keys mstack wrote, so a later uninstall can remove only those.

The same content rules as `mcp/` apply: `${VAR}` placeholders instead of secrets, no machine-specific paths. Cursor has no equivalent file, so these settings are Claude Code only.

No settings are shipped yet.
