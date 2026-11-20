---
name: babysit-pr
description: "Watch a pull request through CI and review until it is ready: wait with one watcher, handle each new failure, review bot finding or human comment, verify findings against the source before changing code, reply with a written reason when dismissing one, keep the PR small, and rebase when the base branch moves. Use for /babysit-pr, babysit this PR, watch this PR, monitor the PR until it is green, or when another skill asks you to babysit the PR."
license: MIT
metadata:
  adapted-from: "skills/babysit-pr in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/babysit-pr). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Babysit PR

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including replies to reviewers and bots, even when the PR discussion is not. (2) **Practices, not domain**: replies cite code, checks and behavior; they never copy business rules, values, URLs or ticket contents beyond what a reply needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Take a pull request from "pushed" to "ready": CI is green, review feedback is handled, and the branch is current. Review bots help even when they are not always right, so treat their findings as claims to check.

This skill does not merge. Whether to merge is decided by the caller (for example [full-send](../full-send/SKILL.md)) or by the user.

## Waiting

Use one watcher per PR, and never a tight loop: every watcher on a GitHub account shares one rate limit.

1. First handle what already exists: failing checks, unresolved threads, new comments.
2. Then wait for the next change with one of these, never two at once on the same PR:
   - **Claude Code:** the `Monitor` tool with an until-loop that polls `gh pr checks <n>` and the PR's comments every 30 seconds or more and prints one line per real change (a check failed, all checks finished, a new comment, review or thread reply from someone other than you, the base moved, the PR merged or closed). Remember what you already reported so a restart does not replay it.
   - **Anywhere else:** `gh pr checks <n> --watch --fail-fast` as one long command, then re-read the PR when it returns.
3. Start the wait again after you push, after you handle an event, and after a resume.

When an event needs no action, end the turn without a message. Never post or say "still waiting".

## GitHub rate limits

`gh pr view`, `gh pr checks` and `gh pr create` use GraphQL. When it is used up, the REST limit is separate and usually has room: read the PR with `gh api repos/<owner>/<repo>/pulls/<n>` and its checks with `gh api repos/<owner>/<repo>/commits/<sha>/check-runs`. If `gh api rate_limit --jq .resources.graphql` shows `remaining` near 0, wait for `reset` with one background command before watching again.

## Reviews

- Act only on checks and comments newer than the latest push.
- Verify every bot finding against the source before changing code. Fix real findings and CI failures, tell repository failures from infrastructure flakes, and rerun a flake once before calling it one.
- When a finding is not worth addressing, reply with a written reason and resolve the thread. Post every comment on the user's behalf with [leave-pr-comments](../leave-pr-comments/SKILL.md).
- If the repo keeps rules for its review bots (a folder of bot instructions), read them before replying to that bot's findings: its findings cite them.
- Advisory bots (those that only comment and gate nothing) get the same checking as any finding, but never wait for them and never hold a merge for them.

## Keep the PR small

Review loops grow a PR one cheap-looking fix at a time. Keep it at the size the goal needs: fix real bugs in the intended case, and decline the rest with a written reason, listed as follow-ups: tests nobody needs, guards for edge cases that do not matter, extra integration or compatibility code, and small performance costs. Prefer the fix that deletes or narrows code.

## Base branch

Watch for changes to the default branch and rebase when they touch this PR's files, or when the PR is behind or in conflict. Force-push only this PR's own branch, with `--force-with-lease`. If another PR makes this one obsolete, stop watching, tell the user, and ask before closing it unless closing was explicitly authorized.

## Stop

Stop when the caller's condition is met: checks green on the latest head, review bots finished, no unresolved threads, and the branch mergeable. Merge only when the user explicitly asked for it; otherwise report that the PR is ready. Right before any merge, `git fetch` and read the PR again. Never merge when it is behind or in conflict, or when base commits that landed after the last green run touch this PR's files: rebase, push, and wait for green again.
