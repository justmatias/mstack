---
name: research
description: "Investigate a question against primary sources (official docs, source code, specs, first-party APIs) in a background agent and save the findings as a cited Markdown file in the repo. Use for /research, research this, gather the docs or API facts for X, or when reading legwork should run while you keep working."
license: MIT
metadata:
  adapted-from: "skills/engineering/research in mattpocock/skills (https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/engineering/research). Thanks to Matt Pocock for the original."
  upstream-commit: "abeeaf95660ba9e8b7c753eb38f441ca707a8823"
  upstream-license: "MIT, Copyright (c) 2026 Matt Pocock, https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/LICENSE"
---

# Research

> **Principles (always apply):** (1) **English only**: the findings file and every note are in English, even when the sources are not. (2) **Practices, not domain**: findings record facts about the question and cite their source; they never copy private business details, credentials or values beyond what the question needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Start a **background agent** with a fresh context to do the reading, so you can keep working while it runs (Claude Code: the Agent tool with `run_in_background`; Cursor: a background subagent). Hand it the question and these instructions.

1. **Primary sources only.** Official documentation, source code, specifications, first-party APIs. Not a blog post or summary that restates them. Trace every claim back to the source that owns it, and say so when a claim has no primary source.
2. **One Markdown file.** Write the findings to a single file, citing the source (URL, file and line, or version) next to each claim.
3. **Where it goes.** Where the repo already keeps such notes, matching its convention. With none, pick a sensible place and tell the user where.

When the agent finishes, report the file path and the two or three findings that matter most, not the whole file.
