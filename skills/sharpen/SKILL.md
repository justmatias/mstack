---
name: sharpen
description: "Make a task deeper, not bigger, then rewrite the prompt: what a top professional would do, the rawest material, the methods and tools, and what independent evidence would show the result is right. Use for /sharpen, make this prompt better, or deepen this task before running it."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/sharpen in cursor/plugins (https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/sharpen). Thanks to Lauren Tan for the original."
  upstream-commit: "aaeb0ea3a0584995aa8f55ce44c6c5259414b896"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/LICENSE"
---

# Sharpen

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the rewritten prompt, even when the source is not. (2) **Practices, not domain**: the rewritten prompt asks for practices and methods, and never copies business names, values or URLs from the original task. Details: [../sync/references/principles.md](../sync/references/principles.md).

I want a deeper version of this task, not a bigger one. Before rewriting it, do four things:

1. Say what a top professional in this field would do here that I'm not asking for.
2. Name the rawest material they would start from instead of what has already been digested for me.
3. Name the specific methods and tools they would use.
4. Say what, other than you or me, would show the result is right.

Then rewrite my prompt to ask for exactly that.

Have the rewritten prompt ask the agent to prototype any choice an experiment can settle and recommend an option based on what it observed. Leave product or preference choices that no experiment can settle for me to make.
