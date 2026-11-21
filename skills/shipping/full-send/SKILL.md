---
name: full-send
description: "Take a task from its current state to a merged pull request without the user watching: finish the smallest change that works, prove it yourself, run a review loop, open the PR, babysit it through CI and review, merge once the merge gate passes, and report the proof and every decision made on the user's behalf. Use only when the user says full send, or asks to take this to a merged PR unattended."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/full-send in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/full-send). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  adapted-from-implement: "skills/engineering/implement in mattpocock/skills (https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/engineering/implement). Thanks to Matt Pocock for the original."
  upstream-commit-implement: "abeeaf95660ba9e8b7c753eb38f441ca707a8823"
  upstream-license-implement: "MIT, Copyright (c) 2026 Matt Pocock, https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/LICENSE"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Full send

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the PR text, replies and the final report, even when the task or the discussion is not. (2) **Practices, not domain**: the PR and the report describe the change and its proof; they never copy business rules, values, URLs or ticket contents beyond what a reader needs to judge it. Details: [../sync/references/principles.md](../sync/references/principles.md).

If the user triggered this, they are not watching the thread, and your updates and final message go unread until long after you stop. You own the work from its current state to a merged PR.

If the user did not clearly ask for a full send, do not assume full autonomy. If they did, everything below applies.

The user grants you permission to:

- merge the PR once the merge gate passes;
- force-push the PR's own branch with `--force-with-lease` after a rebase;
- delete the PR's own branch, local and remote, once the PR is merged;
- use the test methods that the proof needs, without asking first.

## Testing permission

A full send request is the permission. If a project file or other instruction says to ask before a test method, or to leave testing to the user, this request replaces that rule for this task. That covers ask-first rules for computer use, browser automation, simulators and devices, running the app or a dev server, screenshots and visual checks. Use the method that gives direct proof, and list it in the report.

Rules about *how* to test still apply: follow the ones that name the correct command, fixture or check. The permission only removes the ask-first or leave-it-to-the-user step. If a preferred method cannot prove the change, use a gated one. It covers only the tests this task needs: it adds no permission for the steps under "Asking the user", and it does not bypass a harness or system approval prompt if one appears.

## Steps

1. **Finish the change.** Complete the goal with the smallest change that works, and fix the case that happened, not every case that could. If you are on the default branch, create a branch first. If the goal is a ticket reference, fetch it from the issue tracker and state its title before starting; ask when the reference is ambiguous. While working, run the typecheck regularly and single test files often, and the full suite once at the end. When the change works and its code is heavier than it needs to be, run [declutter](../declutter/SKILL.md) on the changed code before step 2.
2. **Prove it.** Get proof for every change you made (see "Proof").
3. **Get feedback.** Run [review-loop](../review-loop/SKILL.md) on the change.
4. **Open the PR** with [open-pr](../open-pr/SKILL.md), after rebasing onto the latest default branch. Add one short line to the description saying how you proved the change.
5. **Babysit it** with [babysit-pr](../babysit-pr/SKILL.md). Fix real findings and CI failures, and get proof for each fix before you push it.
6. **Merge** when the merge gate passes.
7. **Clean up** once GitHub reports the PR as merged: delete its branch (see "Branch cleanup").
8. **Report** in the final message: the PR link, the merge commit, your proof, and each decision you made for the user.

Stay active from step 1 to step 8. If you end your turn while checks or bots are pending, the work stops, because nobody will prompt you again: wait with the watcher from `babysit-pr`, so something wakes you when the PR changes.

## Proof

Proof is evidence you observed yourself in this session: command output, a reproduction, a screenshot. Use the most direct proof the change allows:

- Reproduce the original failure, apply the fix, then watch the same reproduction pass.
- Run the checks the repo's CI runs (typecheck, lint, tests).
- Add one focused test that fails without the fix, when the behavior has none and the repo has a test setup.
- For UI and runtime behavior, run the app and look at the change: green mocked tests do not prove the user experience works. Attach screenshots to the PR when they help and you have a way to upload them.

When you cannot find a way to prove a change, you do not have full confidence. Ask the user.

## Merge gate

Full confidence means all of these are true on the latest commit:

- Your proof covers every change in the diff.
- Required checks are green.
- Review bots have finished, and each finding is fixed or dismissed with a written reason.
- No human review still requests changes.
- The branch is up to date with the default branch, and GitHub reports it as mergeable.

Merge with the method the repo uses: check the allowed methods and recent merged PRs. If the repo uses a merge queue or auto-merge, stay until GitHub reports the PR as merged. Merge through branch protection as configured, and never use `--admin` or any other bypass. You may ignore an automated review that only asks for "human review" when you have high confidence in your changes.

## Branch cleanup

Delete the branch only after GitHub reports the PR as merged, and only the PR's own branch, never the default branch or another one.

- Remote: `git push origin --delete <branch>`, unless the repo already deletes head branches on merge (check that it is gone first).
- Local: switch to the default branch, pull it, then `git branch -D <branch>` (squash merges leave the branch looking unmerged, so `-d` refuses).
- Keep the branch if another open PR still targets it (a stacked PR): retarget that PR first, or leave the branch and say so in the report.
- If the PR was not merged, delete nothing.

## Asking the user

A question in a normal message goes unseen, and the thread looks done. Use the harness's question tool so the thread shows it is waiting (`AskUserQuestion` in Claude Code, the question tool of the harness elsewhere). Put all the context in the question: the PR link, what blocks you, and the options with your recommendation first.

Ask only when you cannot continue alone:

- you cannot prove the change;
- the merge gate cannot pass and you cannot fix that yourself;
- the next step is outside the grant above: deleting data, touching production, changing things outside the repo, closing a PR, or force-pushing any other branch;
- the goal is ambiguous in a way that changes the result;
- another PR makes this one obsolete.

Decide everything else yourself with sensible defaults, and list those decisions in the report. If no question tool is available, or it returns no answer, take the safe path: leave the PR open and unmerged, and start the final message with the question.
