---
name: reflect-rules
description: "Mine the active transcript for coding conventions and durable learnings, and turn each into a prose rule in .cursor/rules plus its automated check (ast-grep, import-linter), or into a skill edit. Spawns parallel review subagents, waits for approval, and routes each rule to the repo or to your personal set. Use when the user says reflect-rules, reflect on the rules, turn my corrections into rules, or make this preference a rule."
disable-model-invocation: true
---

# Reflect rules

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, even when the transcript is not. (2) **Practices, not domain**: extract coding practices only, never business names, rules, values, URLs or verbatim repo code; cite evidence by message index. Details: [../sync-rules/references/principles.md](../sync-rules/references/principles.md).

Mine the current conversation for durable learnings, then route them into rules with checks, or into skill edits.

Invoke when the user says "reflect-rules" or "/reflect-rules". Skip when the conversation is trivial, off-topic, or already covered by an existing rule or skill the parent followed correctly. One-offs are not learnings.

Shared references (always installed together with `sync-rules`): [rule format](../sync-rules/references/rule-format.md), [authoring a check](../sync-rules/references/authoring-a-check.md), [discovery](../sync-rules/references/discovery.md) (including the Claude Code / Cursor tool names).

## 1. Locate the active transcript

Find this conversation's transcript, following "Transcripts" in [discovery.md](../sync-rules/references/discovery.md):

- **Claude Code:** `~/.claude/projects/<slug>/`, where the slug is the workspace path with each `/` and `.` changed to `-`. The newest `.jsonl` directly in that folder is the current session.
- **Cursor:** the `agent-transcripts/` directory the system prompt names.

Do not glob across other projects' folders. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
ls -t <transcripts>/*.jsonl <transcripts>/*/*.jsonl <transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

For each candidate, read the first user message and take the file that contains the conversation's opening prompt. If none matches, pass a tight digest of the session instead. The digest keeps the corrections and decisions in generic terms and drops domain content.

## 2. Spawn the reviewers in parallel

By default, one message with four subagent calls (`Agent` with `subagent_type: "general-purpose"` in Claude Code; `Task` with `subagent_type: generalPurpose`, `readonly: false` in Cursor). Reviewers need MCP access to look up the tickets and threads the transcript references, and read-only modes strip it. Tell each reviewer it must not edit files, and check `git status` afterwards.

With `--light`, spawn only the **conventions** reviewer, then the synthesizer.

Models: if a per-role models rule exists (`~/.cursor/rules/pstack-models.mdc` in Cursor, `~/.claude/rules/pstack-models.md` in Claude Code), set each subagent's model from the role line named below, or the default if the rule or the line is missing. Leave the model unset for `auto` or `inherit-parent`. In Claude Code, map `claude-opus-5-5-xhigh` to `model: "opus"`, `effort: "xhigh"`.

| Lens | Role line | Default model | Prompt template |
|---|---|---|---|
| Judgment | `reflect judgment, divergent, synthesizer` | `claude-opus-5-5-xhigh` | `references/judgment-reviewer.md` |
| Tooling | `reflect tooling` | `claude-opus-5-5-high-fast` | `references/tooling-reviewer.md` |
| Divergent | `reflect judgment, divergent, synthesizer` | `claude-opus-5-5-xhigh` | `references/divergent-reviewer.md` |
| Coding conventions | `reflect conventions` | `claude-opus-5-5-high` | `references/conventions-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their response body and never write files.

## 3. Synthesize

One more subagent, model from the `reflect judgment, divergent, synthesizer` line (default `claude-opus-5-5-xhigh`). Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns Accepted / Rejected / Backlog, where coding conventions are `rule:` rows with a kind and a suggested destination, and anything domain-dependent is rejected with reason `domain`.

## 4. Turn conventions into rules and checks

Unlike pstack's `reflect`, a finding a lint could enforce does not go to Backlog. For each Accepted `rule:` row, prepare the full change now, without writing it yet:

1. **Find the related rule.** Search `.cursor/rules/` (or `~/.cursor/rules/` for personal) for a rule on the same topic. Prefer editing it over adding a duplicate.
2. **Write the prose rule**: the bullet, its `Why:` line, and the `## Checks` line, following [rule-format.md](../sync-rules/references/rule-format.md).
3. **Write the check** for pattern and architecture rows, following [authoring-a-check.md](../sync-rules/references/authoring-a-check.md): YAML, tests with a **synthetic invalid case that reproduces the structure of the chat's code, never the code itself**, then `ast-grep test`, and `scan` to measure existing violations and choose the severity. Judgment rows get `enforcement: llm-review` and no check.
4. **Conflicts.** If the learning contradicts an existing rule, show both side by side (path and line of the existing rule, and the proposed one) and ask which one wins. Never resolve it on your own.
5. **Verify** with `check_no_domain_leak.py` over the prepared files, and reread them for English.

Only what no available tool can check, or what needs a large architecture change, stays in Backlog.

## 5. Approve, then apply

Present the synthesizer's full Accepted / Rejected / Backlog output, with the prepared rule and check for each `rule:` row, and **wait for explicit approval** before applying anything. The user picks the subset, may redirect routings, and **confirms or changes the destination of each rule**:

- **repo**: write to `.cursor/rules/` and `lint-rules/` in the current repo.
- **personal**: write to `~/.cursor/rules/my-<name>.mdc` and `$MY_RULES_HOME`, using the `sync-rules --user` procedure (ids prefixed `my-`, no repo paths). Nothing is written to the repo.

Rules and skills change what every future agent does. Do not auto-apply.

File each Backlog item to the team's tracker (for example `gh issue create`) only after approval, in English and in generic terms.

For skill rows, follow the Routing exactly, as in pstack:

- Never edit a skill under a plugin cache (`plugins/cache/`). Before approval, show its destination (`.claude/skills/<skill>/` or `~/.claude/skills/<skill>/` in Claude Code, `.cursor/skills/<skill>/` or `~/.cursor/skills/<skill>/` in Cursor). After approval, copy the skill folder there and edit the copy.
- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit, `tune description:` or `new skill via create-skill:`: use the environment's skill-creation workflow (Cursor's `create-skill`; in Claude Code, the `skill-creator` skill if installed) instead of inventing the shape ad hoc.

After applying, run `make lint-rules` and `make rules-table` (repo destination) or the personal-set commands from the authoring reference. One commit per rule, Conventional Commits (`feat(rules): add <id> check`). Never open a PR or push.

## 6. Summarize for the user

Short list, no preamble:

- Rules created or edited: `<path>`. The change, one line each, with destination (repo or personal).
- Checks created: `<id>` (severity).
- Skill edits applied: `<skill path>`. One line each.
- Backlog filed: `<issue title>`. One line each.
- Abstracted: what was generalized from the chat.
- Dropped: one line per rejected finding and its reason (including `domain`).

Adapted from pstack/reflect (MIT). See THIRD_PARTY_NOTICES.md
