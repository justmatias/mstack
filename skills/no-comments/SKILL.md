---
name: no-comments
description: "Hunt comments that should not exist with the comment-sicko subagent, fix the accepted findings at the root, and offer to encode claimed constraints as types, tests or lints before deleting their comments. Use for /no-comments, remove the comments, clean up the comments in this diff, or after a change that left narration, banners, commented-out code or workaround notes."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/no-comments in cursor/plugins (https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/no-comments). Thanks to Lauren Tan for the original."
  upstream-commit: "aaeb0ea3a0584995aa8f55ce44c6c5259414b896"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/LICENSE"
---

# No comments

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the report, even when the source is not. (2) **Practices, not domain**: the report names files, symbols and constraints, and never copies business rules, values or URLs from the comments it removes. Details: [../sync/references/principles.md](../sync/references/principles.md).

Spawn the `comment-sicko` subagent (installed from `agents/comment-sicko.md`). Act on accepted findings.

Defer to its fresh perspective. If the subagent is not installed, run the same hunt yourself with the brief in that file.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the base branch, default `main`, including the working tree.

## Steps

1. Spawn `comment-sicko` with the scope. Pick the subagent's reasoning level for the job: a small diff needs less than a whole package.
2. Inspect its report and diff. Reject application-code edits, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat kept intentional code as guilty. Reshape flags on our-code surprises stay actionable. Do not restore those comments. A keep survives only with proof it is about something we cannot change. Audit missed scoped lint and type-checker suppressions. Correctness or safety suppressions stay actionable `MUST KILL`s. Restore deletions only with exact exceptions and scoped proof. Before accepting thin `IMPORTANT` or `do not remove` kills or keeps, trace their symbol or run [why](../why/SKILL.md) on it. If a kill is ambiguous, do not restore. If a keep is refuted or still ambiguous, delete it. Revert and rerun one rejected report with the failure named. Reject a second, report it open, and fail `/no-comments`.
3. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If a fix needs a new shape (a rename, an extraction, a type), sketch it once for the accepted set and its surrounding code, and stop at the sketch. Step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. Fix root causes and redesign from first principles when the shape is wrong, but never widen the fence or fix instances outside it. Never bolt on symptom guards.
5. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. Offer the cheapest in-scope type, runtime, test, or CI lint. Wait for interactive approval. Unattended runs need caller pre-approval. If approved, encode then delete. Otherwise delete, report the constraint open, and sketch out-of-scope work.
6. Report the deletion count, restored comments, reruns, sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work.
