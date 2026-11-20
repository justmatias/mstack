---
name: why
description: "Answer why something works the way it does from the record: the commits and PR discussions that introduced it and each later change. Cited read on design rationale, tradeoffs, regressions, postmortems and data-backed thresholds. Use for /why, why does X work this way, why did we pick Y. Use how for runtime behavior."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/why in cursor/plugins (https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/why). Thanks to Lauren Tan for the original."
  upstream-commit: "aaeb0ea3a0584995aa8f55ce44c6c5259414b896"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/LICENSE"
---

# Why

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the answer, even when the source is not. (2) **Practices, not domain**: the answer cites what the authors wrote about the code, and never copies business rules, values, URLs or ticket contents beyond what the reader needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Answer from the record, not the code: read the commits and PR discussions that introduced the target and each later change, and other sources if the trail is thin. Cite what the authors wrote, mark your own inferences as inferences, and say what the record does not answer.
