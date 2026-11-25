# Agent hooks

Setup merges the fragments under [settings/](../settings/) into
`~/.claude/settings.json`, `~/.cursor/hooks.json` or `$CODEX_HOME/hooks.json`
for the selected editors.
Keep `rulepack` on the editor's PATH. The hooks run only in projects with
`.rulepack.toml`.

- Claude Code's `PostToolUse` runs the scan and exception checks on each file
  written by `Edit` or `Write`. Claude receives the findings immediately.
- Claude Code's `Stop` scans changed files and checks rule coverage. It reports
  findings once per session until they change or a clean stop clears them.
- Cursor's `afterFileEdit` runs the same file checks. Findings appear in Cursor's
  Hooks output channel. [Cursor hooks reference](https://cursor.com/docs/hooks)
- Codex's `PostToolUse` checks every file added, updated or moved by
  `apply_patch`. Codex's `Stop` runs the changed-file scan and coverage check,
  which also catches changes made through shell commands. Review and trust the
  installed hooks through `/hooks` in the CLI or Settings → Hooks in the app.
  [Codex hooks reference](https://learn.chatgpt.com/docs/hooks)

Edit hooks skip files outside `[scan].extensions` or matching `[scan].exclude`.
Each run has a 10-second budget. Set `[hooks].timeout` in `.rulepack.toml` to a
positive number of seconds to override it. A timeout logs a warning and lets
the agent continue.

To disable one hook globally, remove its command entry from the editor's settings.
To disable the hooks for a project, add this to its `.rulepack.toml`.

```toml
[hooks]
enabled = false
```
