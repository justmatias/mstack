---
name: handoff
description: "Compact the current conversation into a handoff document so a fresh agent can pick the work up: goal, state, decisions, open threads and suggested skills, saved outside the workspace with secrets redacted. Use for /handoff, hand this off, write a handoff, summarize this session for another agent, or before ending a long session. Arguments describe what the next session will focus on."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/productivity/handoff in mattpocock/skills (https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/productivity/handoff). Thanks to Matt Pocock for the original."
  upstream-commit: "abeeaf95660ba9e8b7c753eb38f441ca707a8823"
  upstream-license: "MIT, Copyright (c) 2026 Matt Pocock, https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/LICENSE"
---

# Handoff

> **Principles (always apply):** (1) **English only**: the handoff document is in English, even when the conversation was not. (2) **Practices, not domain**: the document records the state of the work and the decisions behind it; it never copies business rules, values, URLs or personal data beyond what the next agent needs to continue. Details: [../sync/references/principles.md](../sync/references/principles.md).

Write a document that summarizes this conversation so a fresh agent can continue the work without it.

1. **Where it goes.** The temporary directory of the user's OS: `$TMPDIR`, else `/tmp` (`%TEMP%` on Windows). Never the current workspace, so nothing lands in the repo. Tell the user the absolute path when done.
2. **What it holds.** The goal, where the work stands, the decisions made and why, what is still open, and the next step.
3. **Suggested skills.** A section naming the skills the next agent should load for this work.
4. **Reference, don't repeat.** Anything already captured in another artifact (a spec, a plan, a decision record, an issue, a commit, a diff) is cited by path or URL, not copied.
5. **Redact.** Remove API keys, passwords, tokens and personal data before writing.
6. **Arguments.** If the user said what the next session is for, tailor the document to that focus.
