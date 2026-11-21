---
name: tdd
description: "Fix a bug test-first: write the smallest regression test that fails for the right reason, then make the smallest fix that turns it green, and report the failing-before and passing-after evidence. Falls back to the closest cheap executable check when a test would be impractical. Use for /tdd, fix this test-first, write a failing test first, add a regression test, or a bug with an obvious cheap local test target."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/tdd in cursor/plugins (https://github.com/cursor/plugins/tree/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/skills/tdd). Thanks to Lauren Tan for the original."
  upstream-commit: "d42aff08aa58965d2735c4ead61a9af82b89d0d0"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/LICENSE"
---

# TDD bug fix

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including test names and the report, even when the bug report is not. (2) **Practices, not domain**: the report names the test and the failure it produced; it never copies business data, values or URLs beyond what the reproduction needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Make the broken behavior executable before changing production code: a focused regression test that fails before the fix and passes after it. Follow the repo's testing rules (in mstack, `rules/testing.mdc`).

Do not force a test when it would be impractical: when it needs broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, vague reproduction steps, or large unrelated fixture churn. Then use the closest useful check instead (below).

## Steps

1. **Understand the bug.** The intended behavior, the current behavior, the affected path and the smallest observable reproduction.
2. **Choose the narrowest executable check.** The closest unit, component or integration test the repo already uses for that path. If no practical path is obvious, do not build a harness from scratch just to follow this workflow.
3. **Write the failing test.** The smallest test that would have caught the bug. It asserts the intended behavior, not the current implementation.
4. **Run it before the fix.** Confirm it fails, and fails for the intended reason. If it passes, or fails for another reason, fix the test or the reproduction before touching production code.
5. **Fix the bug.** The smallest production change that gives the intended behavior and keeps nearby contracts.
6. **Rerun.** Confirm the test passes, then run the tests nearby.

## When a failing test is impractical

Use the closest executable check: a targeted script, a reproduction command, browser automation, a snapshot comparison, a log assertion or a focused integration check.

No new test beats a bad test. A bad test mostly tests mocks, encodes implementation details, depends on timing or unrelated global state, needs expensive infrastructure for a small fix, or would be deleted right after proving the fix.

## Guardrails

- Never change a test to match a wrong implementation.
- Never weaken an existing assertion unless the expected behavior really changed and you say why.
- Keep the test on the bug: no broad fixture churn or unrelated coverage.
- For a flaky bug, make the test deterministic where you can, and say which signal it locks down.
- When the bug exposes a class of failures, land the focused regression test first, then propose coverage for its siblings.

## Reply

Report the evidence, not only the outcome:

- The failing-before test or check, and the failure it produced.
- The passing-after run, and any nearby checks you ran.
- If you could not show a failing-before result, why not, and the closest check you used instead.
