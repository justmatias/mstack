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

`setup-mstack` copies each file to `~/.claude/agents/<name>.md` for Claude Code, or to `~/.cursor/agents/<name>.md` when the user only uses Cursor. Cursor also loads `~/.claude/agents/`, so with both tools there is one copy. The agent's `name` must equal the file name, and `description` must say when to use it.

Shipped agents:

| Agent | Used by | Does |
| --- | --- | --- |
| `comment-sicko` | `no-comments` | Deletes comments that should not exist and flags the code that caused them. It reports and never edits application code. |

Add another only after deciding it belongs on every machine.
