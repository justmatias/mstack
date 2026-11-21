---
name: correct
description: "Find the coding mistakes that keep repeating in this repo (commits, reverts, PR review comments, ast-grep-ignore exceptions, warnings) and make each one impossible. Try architecture first (import-linter), then types and lints (ast-grep, Fixit) whose error names the fix, then a test, and write the .cursor/rules prose last. Prove each check fails on a synthetic copy of a real past mistake. Use for /correct, correct the rules, stop this mistake from happening again, or when the operator keeps correcting the same thing."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/correct in cursor/plugins (https://github.com/cursor/plugins/tree/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/skills/correct). Thanks to Lauren Tan for the original skill."
  upstream-commit: "e58dd043600587dbaf58ba315e7f2b38373eeb43"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/aaeb0ea3a0584995aa8f55ce44c6c5259414b896/pstack/LICENSE"
---

# Correct rules

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, even when commits, comments or reviews are not. (2) **Practices, not domain**: extract coding practices only, never business names, rules, values, URLs or verbatim repo code; cite evidence by sha or PR number. Details: [../sync/references/principles.md](../sync/references/principles.md).

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

Shared references: [rule format](../sync/references/rule-format.md), [authoring a check](../sync/references/authoring-a-check.md), [discovery](../sync/references/discovery.md). The guards run as `mstack <command>` (see the authoring reference).

## Find the mistake classes

First, read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Also read:

- **PR review comments:** `gh pr list --state merged --limit 50 --json number,title` and `gh api repos/{owner}/{repo}/pulls/<number>/comments --jq '.[].body'`.
- **Existing exceptions:** `mstack exceptions --json`. Many exceptions to the same rule mean the rule is wrong or an architecture change is missing.
- **Accumulated warnings:** `mstack lint --only scan --json`, whose `scan.findings` list every finding with its `rule` and `severity`, counted per rule id.
- **Optionally, recent agent transcripts** for this workspace only (see discovery).
- **Search helpers:** `git log --oneline -n 200`, `git log --grep='revert\|fix' -i`, `git log -S '<construct>'`, `rg -n 'workaround|HACK|XXX|do not|don.t use'`.

Group the mistakes into classes. A class counts once it has happened twice.

**Practice mistakes only.** A class that is a business-logic bug ("the discount was computed wrong") produces no rule: report it as `dropped: domain-dependent`. It only counts if a generic practice sits underneath, for example "money computed with `float` instead of `Decimal`". Describe every class in generic terms before going on.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails (an import-linter contract in `.importlinter`). Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types and lints so the bad state can't be written**, but only when the class passes the static-check criteria in step 0 of [authoring-a-check.md](../sync/references/authoring-a-check.md): a concrete construct, decidable from the file alone, expressible as one simple rule. If it fails them, go to level 4; if it is borderline, ask the user before writing anything. Otherwise, if bad code still compiles, add a check whose error names the file, type, or function to use instead: ast-grep for patterns, import-linter for module dependencies, Fixit when logic is needed. Always follow [authoring-a-check.md](../sync/references/authoring-a-check.md). If the pattern is already common, fail only when a change adds more: ship it as `warning` (the full `mstack lint` scan tolerates it, `mstack lint --changed` fails on new or touched code) and open a migration issue.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write docs or agent rules last, for judgment calls and for classes too costly to check statically.** Nothing fails when an agent skips them: mark them `enforcement: llm-review`, and the PR reviewer comments on them.

**Always leave a prose trail, at every level.** Even when the fix is architectural or a lint, create or update the `.mdc` in `.cursor/rules/` with the "why" and its `## Checks` section. The written rule stays as source of truth and index; once a check covers it, shorten it rather than deleting it. (This differs from pstack's `correct`, which drops the rule once its mistake can't happen.)

## Fix and prove

Then fix the most frequent classes now, one commit each, most frequent first, with Conventional Commits messages (`feat(rules): add <id> check`). Prove each new check fails on a real past mistake: read it with `git show <sha>`, rewrite it as a synthetic snippet with generic names (`Foo`, `Item`, `do_work`) that keeps its structure, and make it an `invalid` case. Cite the sha in your reply, never in the test. Run the same command locally and in CI (`mstack lint`). Exceptions go on the offending line with a reason, an expiry date, and a human's approval, in the `rule-exception` format from the rule-format reference. Never invent the approval.

Run `mstack domain-check` over every generated file before committing, and reread everything for English.

## Repeats

When the operator corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that's a repeat, so raise it to the highest level in the same change.

**Reply:** each class with its evidence (commit shas, PR numbers, exception counts), the level you picked, why a higher level didn't work (for llm-review, which static-check criterion failed, or that the user chose it), the files touched, and the severity. Then: abstracted (what was generalized) and dropped (`domain-dependent` classes, one line each).
