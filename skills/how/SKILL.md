---
name: how
description: "Explain how a part of the codebase works so a senior engineer new to it gets a solid mental model: architecture, runtime flow, and placement or ownership questions (where should this live, which package owns this, is this the right layer). Use for /how, how does X work, walk me through this code before I change it. Use why for motivation."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/how in cursor/plugins (https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/how). Thanks to Lauren Tan for the original."
  upstream-commit: "aaeb0ea3a0584995aa8f55ce44c6c5259414b896"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/LICENSE"
---

# How

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the explanation, even when the source is not. (2) **Practices, not domain**: the explanation describes the structure and flow of the code in front of you, with generic names for anything you quote, and never copies business rules, values or URLs beyond what the reader needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Spawn one read-only subagent that explores and explains in one pass (in Claude Code, a read-only general-purpose subagent; in Cursor, a readonly subagent). Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

## 2. Present

Present the subagent's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.
