---
name: modernize
description: "Bring an old pull request up to date and decide honestly whether it should stay open: read the PR's intent, check what landed on the base branch since it diverged (including replacement or competing PRs), pick MODERNIZE, REWORK or CLOSE before pushing, then rebase, compare with git range-diff, run focused checks and push only with --force-with-lease. Never merges, closes or retargets. Use for /modernize, modernize this PR, rebase this PR, update this old PR, is this PR still relevant, or get this stale branch current."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/modernize in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/modernize). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Modernize

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the report and any commit message, even when the PR, its commits or its review threads are not. (2) **Practices, not domain**: the report names the change, the conflicts and the checks; it never copies business rules, values, URLs or ticket contents beyond what the user needs to decide. Details: [../sync/references/principles.md](../sync/references/principles.md).

Modernize the idea, not just the branch. A clean rebase does not prove that the PR still belongs in the product.

## Guardrails

- Fetch the latest origin for the PR branch, the base branch and any other branch related to the work before starting.
- Treat existing worktree changes as the user's. Use a disposable worktree when the active one is dirty or in use for other work.
- Modernizing authorizes rebasing and updating the PR branch. It does not authorize merging, closing, changing the base branch or expanding scope.
- Never use an unqualified force push. Update a rebased branch with `--force-with-lease` against the head SHA observed before the rebase.
- Do not post a PR comment unless the user asked for one. Follow [leave-pr-comments](../leave-pr-comments/SKILL.md) for every comment posted on the user's behalf.

## Establish the PR's intent

Resolve the PR and record its URL, state, base, head repository and branch, current head SHA, author, checks and review state. Read the title, body, linked issues, commits, review threads and the complete diff. State the smallest coherent goal the PR was trying to accomplish before judging its implementation.

Fetch the latest remote base and PR head. Use the PR's actual base branch, usually the default branch, rather than assuming the local one is current. Record the merge base so the original PR and the later base-branch changes can be compared separately.

## Check what changed around it

Inspect the commits and diffs added to the base branch since the PR diverged. Search merged and open PRs when titles, code paths or behavior suggest a replacement or a competing implementation.

Look beyond overlapping lines:

- Has the same user-facing problem already been solved?
- Did APIs, types, schemas, dependencies or architectural boundaries change?
- Do both sides now claim ownership of the same behavior or invariant?
- Was the code being changed deleted, moved or intentionally simplified?
- Would landing the PR restore an old behavior or create two ways to do the same thing?
- Is the original benefit still large enough to justify the maintenance cost?

Do not call a PR current merely because Git reports no conflicts.

## Choose a disposition before pushing

| Disposition | When | What to do |
| --- | --- | --- |
| **MODERNIZE** | The goal is still useful and the implementation is still the right shape. | Rebase, resolve conflicts, test and update the branch. |
| **REWORK** | The goal is still useful, but a mechanical rebase would keep the wrong implementation. | Explain the smallest credible rewrite and stop before pushing, unless the user also asked for the rework. |
| **CLOSE** | The PR is superseded, obsolete, directionally wrong or no longer worth its cost. | Cite concrete evidence and stop. Do not rebase an obsolete branch, and do not close it without explicit permission. |

Be willing to recommend CLOSE. Age alone is not evidence, and sunk effort is not a reason to keep a PR alive.

## Rebase without losing intent

For a MODERNIZE disposition:

1. Create a safe local branch or disposable worktree at the recorded PR head.
2. Rebase its commits onto the freshly fetched base branch.
3. Resolve each conflict by the PR's current intent and the base branch's newer invariants. If a conflict reveals a product or architecture disagreement, stop and reconsider the disposition instead of guessing.
4. Compare the commit series before and after with `git range-diff` and inspect the final diff. Confirm that no intentional behavior disappeared and no already-landed behavior came back.
5. Run the repository's focused checks for the touched area. Tell real failures apart from pre-existing or infrastructure ones.
6. Push with `--force-with-lease` tied to the previously observed remote head. If the lease fails, fetch and reassess rather than overwrite new work.

Do not merge the PR.

## Report

Lead with `MODERNIZE`, `REWORK` or `CLOSE` and the reason. Then summarize:

- the meaningful changes on the base branch;
- conceptual conflicts, or confirmation that none were found;
- the rebase and push result, if performed;
- the checks run and their results;
- the remaining decision or work, with a link to the PR.

Separate observed facts from judgment. Say what could not be verified instead of manufacturing confidence.
