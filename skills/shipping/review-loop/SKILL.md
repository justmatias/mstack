---
name: review-loop
description: "Use an independent reviewer to improve a change or challenge a consequential proposal. Run one fresh-context reviewer per round, check every finding, apply the smallest fix or push back with evidence, and track outcomes. Use for /review-loop, review loop, loop a reviewer over this change, challenge this decision with an independent reviewer, or when another skill asks for a review loop."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "skills/sol-loop in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/sol-loop). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
  adapted-from-doubt-driven-development: "skills/doubt-driven-development in addyosmani/agent-skills (https://github.com/addyosmani/agent-skills/tree/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee/skills/doubt-driven-development). Thanks to Addy Osmani for the original."
  upstream-commit-doubt-driven-development: "8c99fa36d90068c82d547f7c12a9d67a3e95f4ee"
  upstream-license-doubt-driven-development: "MIT, Copyright (c) 2025 Addy Osmani, https://github.com/addyosmani/agent-skills/blob/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee/LICENSE"
---

# Review loop

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the reviewer brief, the findings log and the PR blurb, even when the diff or the discussion is not. (2) **Practices, not domain**: briefs and findings name coding practices and cite file and line; they never copy business rules, values, URLs or ticket contents beyond what a finding is about. Details: [../sync/references/principles.md](../sync/references/principles.md).

Make a change more correct by having an independent reviewer check it in a loop, then answering each finding with the smallest fix that works. Make the fewest changes that satisfy the reviewer: watch for scope creep and push back when a finding asks for more than the intent needs.

Use the decision mode below to challenge a proposal or test an assumption while the decision is still open. For a read-only report on two axes (the repo's rules and the spec), use [diff-review](../diff-review/SKILL.md).

## Budget

- Default: 3 rounds. Round 1 reviews the whole change; later rounds check only changed code and open findings.
- Extend to 5 only for security, permissions, auth, data loss or state and concurrency, while a blocker or should finding stays open with evidence, or when the user asks.
- Stop early when a round returns only nits. Declined nits and comment-, doc- or format-only fixes need no new round.
- One reviewer at a time, and the reviewer starts no subagents of its own.
- Keep a findings log with each finding's id, severity and outcome. Record usage only if the tool returns it; never guess it.

## 1. Scope

1. Run `git status --short`. Never stash, discard or include unrelated changes. Limit the review to the change's paths when they separate cleanly; otherwise stop and ask.
2. Run `git fetch origin`, then find the base.
   - PR: `gh pr view <n> --json baseRefName,headRefOid`. Check out the branch only when `git status --short` returns nothing, and confirm `HEAD` is the PR head or ahead of it only by this change. Base: `git merge-base HEAD origin/<baseRefName>`.
   - Local: `git merge-base HEAD origin/<default-branch>`. With no remote, use a base the user names, or `HEAD` for uncommitted changes only.
3. The change is the base against the working tree in those paths, untracked files included. Use one diff command for every round.
4. Write the intent and what is out of scope in one or two sentences. Run the checks that cover the change, and do not send code this change breaks. Note missing or already failing checks in the brief.
5. **Trace the stated requirements.** Read the linked issue, spec, or acceptance criteria when the change references one. Give the reviewer the relevant requirements and ask it to check each against the diff. If no written requirements exist, state that in the brief and review the user's stated intent.

## 2. Start the reviewer

Choose the reviewer from what this machine offers, then let the user pick:

1. **Discover candidates.**
   - Agent types the harness lists for the `Agent` tool in Claude Code (and `ListAgents` for running sessions), custom agents in `.claude/agents/` and `~/.claude/agents/`, or `Task` subagent types in Cursor. Keep read-only reviewers, or ones whose tools you can restrict to read-only.
   - Other models' CLIs on `PATH` (check with `command -v`, never run them to probe), only when they have a non-interactive, read-only review mode.
     Close stdin when you run one (`< /dev/null`): some, such as `codex exec`, otherwise wait for input and never reply.
2. **Ask which to use** with the harness's question tool (`AskUserQuestion` in Claude Code), listing each candidate with one line on what it is, and put your recommendation first: a reviewer from a different model family than the author when one exists, since it catches more than the author's own model; otherwise a fresh-context `general-purpose` subagent (`Agent` in Claude Code, `Task` with `subagent_type: generalPurpose` and `readonly: true` in Cursor). Skip the question when the user already named a reviewer, or when the only candidate is the fresh-context subagent.
3. **Record it.** Use exactly the chosen reviewer, note its name and version when it reports them, and say in the report when it is the same model family as the author.

Never hardcode a model id. Do not edit the scoped files while a round runs, do not poll, and do not start a second reviewer. On timeout, error or no reply, cancel the round, confirm it stopped, and restart with the findings log.

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

Update the findings log, re-run the checks, and compare `git diff --shortstat <base>` with the previous round. If the review grew the diff, cut something first. Never agree just to end the loop.

## 4. Next round

Start another round only when budget remains and a blocker or should finding is open, behavior code changed, or the last approval does not cover the current behavior diff. Send a fresh reviewer the round 1 brief, the findings log (`fixed:`, `disagree:`, `declined:` with evidence), the same base diff and what changed since. Tell it to look at open ids and changed code only, and to mark each old id `resolved` or `still open: <reason>`.

## 5. Stop

- **Agreed:** APPROVE on the current behavior diff, no blocker or should open, and no concern of your own.
- **Stuck:** two replies leave a finding unresolved, or the budget ended. Show both sides in two or three lines each and let the user decide. The end of the budget is not approval.

Do not push during the loop. Once the review is approved, push only when the user asked to push, ship or update the PR. When you push to a PR, add this line to its description: `Reviewed with review-loop: <N> rounds with <reviewer>. Verdict: approved`.

## Report

Rounds, reviewer, what it changed, initial and final diff size, fixed and declined findings with reasons, usage if the tool returned it (otherwise say it did not), and whether anything was pushed.

## Review a proposed decision

Use this mode for one consequential decision, such as a change to a module boundary or an assumption about ordering that the compiler cannot check. Skip the diff setup and use the reviewer selection in step 2.

1. **State the claim privately.** Write what you expect to hold and what happens if it fails. Pick the smallest proposal, code excerpt or body of evidence that can be reviewed independently.
2. **Ask the reviewer to find counterexamples.** Send the material, the requirements it must satisfy and relevant evidence, including evidence that could invalidate the claim. Withhold your conclusion and reasoning. Ask for concrete cases where a requirement fails, with evidence for each finding.
3. **Check each finding.** Clarify requirements if the brief was incomplete. Fix real issues, record any trade-off you accept, and give evidence when dismissing a finding. For a behavioral claim, a focused executable check may resolve a finding directly.
4. **Limit the review to three rounds.** Use a fresh reviewer when the material or its requirements have changed. Report which claims held up and which substantive findings remain open when you stop.
