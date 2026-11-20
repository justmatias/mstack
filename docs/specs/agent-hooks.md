# Agent hooks that run the checks

- **Phase:** next
- **Depends on:** `agent-config-folders` (hooks ship in `settings/` and are merged on install), `runtime-lint-command` (`mstack lint --files`).

## Problem

The checks run at commit time (pre-commit) and in CI. An agent that breaks a rule finds out only at the end, after building more code on top of the mistake, or not at all if it never commits. "Rules as checks" works best when the check answers while the agent is writing.

## Goal

User-level hooks that run the repo's own checks on each file the agent edits and feed the errors back to the agent, only in repos that opted in.

## Out of scope

- Hooks that run the full test suite or slow steps after every edit.
- Hooks for repos without mstack.

## Design

**Opt-in by repo:** the hook does nothing unless the repo has `.mstack.toml`. A user-level hook then stays silent in unrelated projects.

**Hooks** (Claude Code; each in `hooks/` with its settings fragment in `settings/claude.json`):

| Event | Matcher | Runs | On failure |
| --- | --- | --- | --- |
| `PostToolUse` | `Edit\|Write` | `mstack hook post-edit`: reads the hook JSON from stdin, takes `tool_input.file_path`, runs `mstack lint --files <file> --only scan exceptions` | exit 2 with the findings on stderr, so the agent sees them and fixes them |
| `Stop` | none | `mstack hook stop`: `mstack lint --changed --only scan coverage` | exit 2 with a summary once; does nothing if the previous stop already reported the same findings (avoids loops) |

- `mstack hook` is a CLI subcommand, not a shell script, so it works on every platform (`portability`).
- Each run has a time budget (default 10 seconds, configurable in `.mstack.toml` `[hooks].timeout`). If it runs out, the hook passes and logs a warning instead of blocking the agent.
- Files outside `[scan].extensions` or in the scan excludes return immediately.
- **Cursor:** check its current hooks support (an after-file-edit event) at implementation time, and add an equivalent entry if it exists.

## Changes

- `src/mstack/hooks.py` (`post-edit`, `stop`), registered as `mstack hook`.
- `settings/claude.json`: the `hooks` entries.
- `hooks/README.md`: what each hook does, how to disable one (remove its settings entry, or set `[hooks] enabled = false` in a repo's `.mstack.toml`).

## Tests

- `post-edit` with sample hook JSON: a violating file exits 2 and prints the finding; a clean file exits 0; a repo without `.mstack.toml` exits 0 without running ast-grep; an excluded file exits 0; a timeout passes.
- `stop` reports once, and stays silent on a repeat with the same findings.

## Docs

- `README.md`: one line on what the hooks do, and that they only act in repos with `.mstack.toml`.

## Acceptance criteria

- [ ] In an opted-in repo, an agent that writes `print(...)` in application code sees the `no-print-in-app` finding right after the edit.
- [ ] In any other repo, the hooks add no visible output and under 100 ms per edit.
