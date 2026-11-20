---
name: full-stop
description: "Do the same unattended work as full-send, but stop with the pull request ready for the user to merge, and never merge it: prove the change, run the review loop, open and babysit the PR, make sure no auto-merge or merge queue can merge it, then hand off with the proof and the readiness verdict. Use only when the user says full stop, even as a closing 'Full stop.' that reads like emphasis, or asks to take this to a merge-ready PR unattended."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/full-stop in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/full-stop). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Full stop

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the PR text, replies and the handoff report, even when the task or the discussion is not. (2) **Practices, not domain**: the PR and the report describe the change and its proof; they never copy business rules, values, URLs or ticket contents beyond what a reader needs to judge it. Details: [../sync/references/principles.md](../sync/references/principles.md).

Do the same work as [full-send](../full-send/SKILL.md), but stop with the PR ready for the user to merge. Never merge it.

Read full-send and follow its steps, proof rules, review and babysitting. A clear "full stop" request authorizes that work without a separate "full send" request, including full-send's testing permission: use the test methods the proof needs directly, even when a project file says to ask first. Full-send's merge permission does not apply, and the overrides below take precedence.

## No merging

You may commit, push, rebase, fix conflicts and use `--force-with-lease` on this task's branch. Never merge, enable auto-merge, enter a merge queue, push to the default branch, bypass branch protection, or delegate any of those.

Disable existing auto-merge and take the PR out of any merge queue before work begins, and check again before each push. Report those changes. If you cannot prevent automatic merging, report the blocker before going on.

## Stop at the gate

Use full-send's merge gate as the readiness check, and replace its merge and final report steps with a handoff. Proof and review must cover the final diff: recheck behavior changes and meaningful conflict fixes before handing off.

Fetch the target branch and check the live PR's head, base, checks, reviews and mergeability. Confirm it is open, not a draft, and not set to merge without the user. If someone else merged it, report that instead. Then pick one verdict:

- **Ready to merge:** the merge gate passes. Leave the PR open and unmerged.
- **Waiting for required approval:** only human approval remains. Confirm that this is the actual blocker.
- **Blocked:** explain what prevents readiness, what you tried and what is needed, and follow full-send's rules for asking the user.

Report the PR link, the final head, the verdict, the proof, the reviewer outcome and the remaining risks, and say whether the PR is still open and unmerged.
