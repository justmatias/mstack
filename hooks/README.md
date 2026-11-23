# Agent hooks

Setup merges the fragments under [settings/](../settings/) into
`~/.claude/settings.json` and `~/.cursor/hooks.json` for the selected editors.
Keep `mstack` on the editor's PATH. The hooks run only in projects with
`.mstack.toml`.

- Claude Code's `PostToolUse` runs the scan and exception checks on each file
  written by `Edit` or `Write`. Claude receives the findings immediately.
- Claude Code's `Stop` scans changed files and checks rule coverage. It reports
  findings once per session until they change or a clean stop clears them.
- Cursor's `afterFileEdit` runs the same file checks. Findings appear in Cursor's
  Hooks output channel. [Cursor hooks reference](https://cursor.com/docs/hooks)

Edit hooks skip files outside `[scan].extensions` or matching `[scan].exclude`.
Each run has a 10-second budget. Set `[hooks].timeout` in `.mstack.toml` to a
positive number of seconds to override it. A timeout logs a warning and lets
the agent continue.

To disable one hook globally, remove its command entry from the editor's settings.
To disable mstack's hooks for a project, add this to its `.mstack.toml`.

```toml
[hooks]
enabled = false
```
