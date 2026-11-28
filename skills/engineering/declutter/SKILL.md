---
name: declutter
description: "Simplify code that already works without changing what it does: understand why each piece exists first, look for concrete complexity signals (deep nesting, long functions, nested ternaries, flag parameters, dead code, needless wrappers), apply one change at a time with the tests run after each, and compare before and after. The repo's own rules always win over a signal. Use for /code-simplification, simplify this, clean up this function, reduce the nesting, make this easier to read, or after a feature works but its code is heavier than it needs to be."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/code-simplification in addyosmani/agent-skills (https://github.com/addyosmani/agent-skills/tree/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee/skills/code-simplification). Thanks to Addy Osmani for the original."
  upstream-commit: "8c99fa36d90068c82d547f7c12a9d67a3e95f4ee"
  upstream-license: "MIT, Copyright (c) 2025 Addy Osmani, https://github.com/addyosmani/agent-skills/blob/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee/LICENSE"
---

# Code simplification

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including identifiers, comments and commit messages, even when the code around it is not. (2) **Practices, not domain**: you change how code expresses its logic, never the business rules, values or names it encodes; renames describe what a thing holds, in the repo's own vocabulary. Details: [../sync/references/principles.md](../sync/references/principles.md).

Make working code easier to read, change and debug, while it keeps doing exactly what it did. Fewer lines is not the goal: the test for every change is whether a new contributor would understand the result faster than the original.

This skill edits files. It does not commit unless the user asks.

| Invocation | Scope |
| --- | --- |
| `declutter` | The code changed on the current branch (`git diff <merge-base>...HEAD`) plus uncommitted changes |
| `declutter <path or symbol>` | That file, folder or function only |
| `declutter --report` | Same scope, but only list the opportunities; change nothing |

**When not to use it:** the code is already clear, you do not yet understand it, the simpler version would be measurably slower on a hot path, or the module is about to be rewritten.

## Principles of the change

1. **Behavior stays identical:** same outputs, errors and side effects in the same order. Existing tests pass unedited. If unsure a change preserves behavior, do not make it.
2. **The repo's conventions win** over any signal below. Simplifying means matching the codebase, not your preferences.
3. **Clarity over cleverness, and no over-simplifying.** Do not inline a helper that names a concept, merge simple functions into a complex one, or remove an abstraction that exists for testability.
4. **Stay in scope.** No drive-by refactors unless the user widens it.

## 1. Collect the conventions

1. Read every `.mdc` in the `rules_dir` set in `.mstack.toml` (default `.cursor/rules/`), plus `AGENTS.md`, `CLAUDE.md` and `.claude/rules/*.md` when they exist (see [../sync/references/discovery.md](../sync/references/discovery.md)). Keep the rules whose `globs` match a file in scope.
2. Read the code next to the target: how it orders imports, declares functions, names things, handles errors and annotates types. Match that.

## 2. Understand before touching

Before changing or removing anything, find out why it is there (Chesterton's fence): its job, callers and callees, edge cases and the tests that pin them, and why it may look this way (performance, a platform constraint, a past bug: `git blame` or `git log -L` often says). If you cannot answer, read more. Code with no tests around the behavior you would touch gets a test first, or is left alone and reported.

## 3. Find the opportunities

Each signal is concrete. A repo rule that endorses the pattern wins; a linter that already enforces it makes it out of scope.

Start from [the review smell baseline](../diff-review/references/smell-baseline.md) (duplicated code, mysterious names, middle men, speculative generality and the rest): each one is also a simplification opportunity, and its usual fix is the change to make. Then add these signals, which are about how a single function reads:

| Signal | What to look for | Usual simplification |
| --- | --- | --- |
| Deep nesting | Three or more levels of `if`/loop | Guard clauses that return or raise early |
| Long function | Fifty or more lines doing several jobs | Split into functions named for each job |
| Nested ternary | A conditional expression inside another | `if`/`elif`, a `match`, or a lookup table |
| Flag parameter | Calls like `do_work(foo, True, False)` | Separate functions, or keyword-only named options |
| Dead code | Unreachable branches, unused variables or imports, commented-out blocks | Delete it, after confirming nothing reaches it |
| Redundant cast or assertion | Converting to a type the value already has | Remove it |
| Misleading name | A `get_` that also mutates, a `is_` that returns a value | Rename to what it does |
| Comment that restates the code | `# add one` above `count += 1` | Delete it. Keep comments that explain why |
| Verbose construct | Building a list or dict in a loop, `if cond: return True else: return False` | The language's direct form (a comprehension, `return cond`) |

Judgment calls (state passed through many layers, an abstraction that might be load-bearing) are flagged to the user, not refactored on your own.

With `--report`, list the opportunities by file and line, with the signal and the proposed change, and stop here.

## 4. Apply one change at a time

For each simplification:

1. Make the one change.
2. Run the tests that cover it (the full suite when unsure), and the repo's linters (`make lint`, `make lint-rules-changed`, or what `AGENTS.md` names).
3. Pass: keep it and go on. Fail: revert it and reconsider; never edit a test to make a simplification pass.

Never batch several untested simplifications: when something breaks, you need to know which one did it. A change that would touch hundreds of lines is a job for a codemod or an AST rewrite (ast-grep `fix:`, for example), not for hand edits.

Keep refactoring apart from feature and bug-fix work: if the user commits, simplifications go in their own commits (`refactor(<scope>): ...`), never mixed into a feature commit.

## 5. Compare before and after

Look at the whole diff: is it easier to understand, not just shorter; does it introduce a pattern the codebase does not use; is it reviewable with nothing unrelated mixed in? Revert any simplification that made code harder to follow.

**Red flags.** Stop and reconsider when:

- a test had to change for it to pass;
- error handling was removed or weakened;
- a rename follows your taste, not the repo's conventions;
- you simplified code you do not fully understand;
- you kept an abstraction only because "it might be useful later" (if nothing uses it now, it goes), or removed one without checking why it existed.

## 6. Reply

A short list. Leave out empty lines:

- Scope: what was simplified (files, or the ref range).
- Changes: one line each, with its signal (for example "`handle`: nested checks → guard clauses").
- Flagged, not changed: the judgment calls, and code left alone for lack of tests.
- Checks: the test and lint commands run and their result. Confirm no test was edited, and no error handling was removed.

When the same signal keeps coming back across runs and a check could catch it mechanically, say so in one line and suggest [correct](../correct/SKILL.md) or [sync](../sync/SKILL.md) to turn it into a check.
