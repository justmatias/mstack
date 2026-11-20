# Agents

Subagent definitions, one Markdown file each: `agents/<name>.md`.

```markdown
---
name: <name>          # must equal the file name
description: <when the main agent should hand work to this subagent>
tools: Read, Grep     # optional (Claude Code); Cursor ignores it
model: inherit        # optional
---

The subagent's prompt.
```

`setup-mstack` copies each file to `~/.claude/agents/<name>.md` for Claude Code, or to `~/.cursor/agents/<name>.md` when the user only uses Cursor. Cursor also loads `~/.claude/agents/`, so with both tools there is one copy. `mstack config-check` checks that `name` equals the file name and that `description` is there.

No agents are shipped yet. Add one only after deciding it belongs on every machine.
