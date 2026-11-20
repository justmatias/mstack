---
name: review-loop
description: "Make a change more correct before (or after) its pull request by looping an independent reviewer over it: pin the diff, run one fresh-context reviewer per round, check every finding yourself, apply the smallest fix or push back with evidence, keep a ledger, and stop on approval, on a stuck dispute, or when a small round budget ends. Use for /review-loop, review loop, loop a reviewer over this change, get an independent review and fix what it finds, or when another skill asks for a review loop."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/sol-loop in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/sol-loop). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Review loop

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the reviewer brief, the ledger and the PR blurb, even when the diff or the discussion is not. (2) **Practices, not domain**: briefs and findings name coding practices and cite file and line; they never copy business rules, values, URLs or ticket contents beyond what a finding is about. Details: [../sync/references/principles.md](../sync/references/principles.md).

Make a change more correct by having an independent reviewer check it in a loop, then answering each finding with the smallest fix that works. Make the fewest changes that satisfy the reviewer: watch for scope creep and push back when a finding asks for more than the intent needs.

This skill fixes code. For a read-only report on two axes (the repo's rules and the spec), use [review](../review/SKILL.md).

## Budget

- Default: 3 rounds. Round 1 reviews the whole change; later rounds check only changed code and open findings.
- Extend to 5 only for security, permissions, auth, data loss or state and concurrency, while a blocker or should finding stays open with evidence, or when the user asks.
- Stop early when a round returns only nits. Declined nits and comment-, doc- or format-only fixes need no new round.
- One reviewer at a time, and the reviewer starts no subagents of its own.
- Keep a ledger: finding id, severity, outcome. Record usage only if the tool returns it; never guess it.

## 1. Scope

1. Run `git status --short`. Never stash, discard or include unrelated changes. Limit the review to the change's paths when they separate cleanly; otherwise stop and ask.
2. Find the base after `git fetch origin`:
   - PR: `gh pr view <n> --json baseRefName,headRefOid`. Check out the branch only when the tree is clean, and confirm `HEAD` is the PR head or ahead of it only by this change. Base: `git merge-base HEAD origin/<baseRefName>`.
   - Local: `git merge-base HEAD origin/<default-branch>`. With no remote, use a base the user names, or `HEAD` for uncommitted changes only.
3. The change is the base against the working tree in those paths, untracked files included. Use one diff command for every round.
4. Write the intent and what is out of scope in one or two sentences. Run the checks that cover the change, and do not send code this change breaks. Note missing or already failing checks in the brief.

## 2. Start the reviewer

Choose the reviewer from what this machine offers, then let the user pick:

1. **Discover candidates.**
   - Agent types the harness lists for the `Agent` tool in Claude Code (and `ListAgents` for running sessions), custom agents in `.claude/agents/` and `~/.claude/agents/`, or `Task` subagent types in Cursor. Keep read-only reviewers, or ones whose tools you can restrict to read-only.
   - Other models' CLIs on `PATH` (check with `command -v`, never run them to probe), only when they have a non-interactive, read-only review mode.
2. **Ask which to use** with the harness's question tool (`AskUserQuestion` in Claude Code), listing each candidate with one line on what it is, and put your recommendation first: a reviewer from a different model family than the author when one exists, since it catches more than the author's own model; otherwise a fresh-context `general-purpose` subagent (`Agent` in Claude Code, `Task` with `subagent_type: generalPurpose` and `readonly: true` in Cursor). Skip the question when the user already named a reviewer, or when the only candidate is the fresh-context subagent.
3. **Record it.** Use exactly the chosen reviewer, note its name and version when it reports them, and say in the report when it is the same model family as the author.

Never hardcode a model id. Do not edit the scoped files while a round runs, do not poll, and do not start a second reviewer. A timeout, an error or no reply is not approval: cancel, confirm it stopped, and restart with the ledger.

Round 1 brief (a fresh reviewer has no history, so paste everything):

```text
Review only. Do not edit, commit, push, comment on PRs or start subagents.
Repo: <absolute path>  Base: <sha>  Intent: <intent>  Out of scope: <scope>
Checks: <results>
See: git diff <base> [-- <paths>]; git status --short (read untracked files).
Read the surrounding code. Find bugs, broken callers and mismatches with the
intent. Skip style unless it hides a bug. Hold the change to the smallest size
that works: flag code, tests or guards the intent does not need. Other paths,
rare cases, small performance costs and extra compatibility are nits.
blocker = the intended case is wrong.
should  = a real bug that callers will hit, inside the intent.
nit     = everything else.
Reply:
VERDICT: APPROVE or CHANGES
S1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion>   (stable ids)
```

## 3. Answer the findings

Check each finding and its severity yourself. Another path, a rare case or a small cost is a nit, whatever label it came with.

- **Agree:** apply the smallest fix. Prefer deleting or narrowing over a new lock, cache, helper or option, and fix the case that happened. Add one focused test that fails without the fix when the intent needs it.
- **Disagree:** say why, with evidence (`file:line`, a test, command output).
- **Out of scope or a nit:** decline in one line and list it as a follow-up.

Update the ledger, re-run the checks, and compare `git diff --shortstat <base>` with before. If the review grew the diff, cut something first. Never agree just to end the loop.

## 4. Next round

Start another round only when budget remains and a blocker or should finding is open, behavior code changed, or the last approval does not cover the current behavior diff. Send a fresh reviewer the round 1 brief, the ledger (`fixed:`, `disagree:`, `declined:` with evidence), the same base diff and what changed since. Tell it to look at open ids and changed code only, and to mark each old id `resolved` or `still open: <reason>`.

## 5. Stop

- **Agreed:** APPROVE on the current behavior diff, no blocker or should open, and no concern of your own.
- **Stuck:** a finding is still disputed after two replies, or the budget ended. Show both sides in two or three lines each and let the user decide. The end of the budget is not approval.

Do not push during the loop. After agreement, push only when the user asked to push, ship or update the PR. When you push to a PR, add above the model attribution line: `Reviewed with review-loop: <N> rounds with <reviewer>. Verdict: approved`.

## Report

Rounds, reviewer, what it changed, diff size before and after, fixed and declined findings with reasons, usage if the tool returned it (otherwise say it did not), and whether anything was pushed.
