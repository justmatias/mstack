---
name: grill-me
description: "Interview the user relentlessly about a plan, design or decision until you share one understanding, asking in rounds: every question whose prerequisites are settled, each with your recommended answer. Facts you can look up are your job, decisions are theirs. Use for /grill-me, grill me, stress-test this plan, poke holes in this design, or when another skill needs to walk a decision tree with the user."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/productivity/grill-me and skills/productivity/grilling in mattpocock/skills (https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/productivity/grill-me and skills/productivity/grilling). Thanks to Matt Pocock for the original."
  upstream-commit: "abeeaf95660ba9e8b7c753eb38f441ca707a8823"
  upstream-license: "MIT, Copyright (c) 2026 Matt Pocock, https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/LICENSE"
---

# Grill me

> **Principles (always apply):** (1) **English only**: every question, recommendation and summary is in English, even when the plan or the discussion is not. (2) **Practices, not domain**: questions probe the decision and its trade-offs; they never copy business rules, values or URLs beyond what the plan itself contains. Details: [../sync/references/principles.md](../sync/references/principles.md).

Interview the user about a plan until you both hold the same picture of it. Treat the plan as a **decision tree**: every decision has follow-up decisions that only make sense once it is settled.

## Rounds

1. List the open decisions. The **frontier** is every decision whose prerequisites are already settled, meaning the questions you can ask now without guessing answers you have not heard.
2. Ask the whole frontier in one round. Number the questions, and give each a short title, the question itself (with the options when it is a choice), and your recommended answer.
3. Word each question so that "yes" accepts your recommendation.
4. Wait for the answers. Do not continue on assumed answers.
5. Recompute the frontier: settled decisions unblock the questions that depended on them. A question that depends on another one still open in this round belongs to a later round.

Example of one question in a round:

```
Q1. Storage: keep Foo records in the existing table or add a new one?
Recommended: the existing table, because Foo has the same lifecycle as Item.
```

## Facts are yours, decisions are theirs

- Never ask the user for something you can look up: files, configuration, history, docs. When a frontier question needs such a fact, send a subagent with a fresh context to find it (in Claude Code, the Agent tool; in Cursor, a subagent).
- A running lookup is an unsettled prerequisite, so only the questions that depend on it wait. Ask the rest of the frontier now.
- The decisions themselves go to the user, one recommendation each, and you wait.

## Done

The session is done when the frontier is empty: every branch visited and nothing left silently assumed. Summarize the settled decisions, and do not act on them until the user confirms the shared understanding.
