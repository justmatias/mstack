# Engram as an optional memory server

- **Phase:** future
- **Depends on:** nothing open. Ships through `mcp/`, which `setup-mstack` already installs.

## Problem

mstack keeps what should be **enforced** (rules and checks) and **how to work** (skills). What agents **learn while working** (decisions, gotchas, how a project is laid out) stays in each tool's own memory and is lost between tools. Claude Code's built-in memory covers it for Claude Code alone, but Cursor, Codex and the others don't share it. [Engram](https://github.com/Gentleman-Programming/engram) (MIT) is a single binary that stores agent memories in local SQLite with full-text search and exposes them over MCP to Claude Code, Cursor, Codex, Gemini CLI and others.

## Goal

A machine that uses more than one agent can opt into Engram as a shared memory, wired in by `setup-mstack` like any other MCP server, and `reflect` can use what it holds as evidence for a new rule.

## Out of scope

- Replacing rules or skills with memories. A memory is a hint an agent may retrieve; a rule with a check is enforced.
- Replacing Claude Code's built-in memory. Engram runs next to it.
- Installing the Engram binary, hosting Engram Cloud, or syncing memories across machines (`engram sync`). Memories hold project details, and this repo holds practices only.
- Separate databases per machine role. Use `ENGRAM_DATA_DIR` on that machine if needed.

## Design

**What goes where:**

| Kind of knowledge | Lives in | Enforced |
| --- | --- | --- |
| A convention that can be checked | rule + check | yes, by `rulepack lint` |
| A convention that needs judgment | rule with `llm-review` | in review |
| A workflow | skill | when invoked |
| A project fact, decision or gotcha | memory (built-in or Engram) | no, retrieved on demand |

- **Wiring:** `mcp/engram.json` (`engram mcp --tools=agent`), installed by `setup-mstack` like any other `mcp/` file, so its plan and backups cover it. The setup offers it only when `engram` is on `PATH`, and otherwise mentions it with the official install link. If the user already ran `engram setup <agent>`, the setup sees the existing `engram` server and keeps it: never both for the same agent.
- **Promotion into rules (`reflect`, `correct`):** a new optional source in `discovery.md`. When the Engram MCP tools are available, search the current project's memories for corrections and conventions. A convention that comes up repeatedly counts as evidence, like a repeated correction in a transcript, and goes through the same principles (abstracted, no domain). The reply suggests removing the memory once a rule covers it, so the two don't diverge.

## Changes

- `mcp/engram.json`.
- `.agents/skills/setup-mstack/SKILL.md`: offer it only when `engram` is on `PATH`, and keep an existing `engram` server.
- `skills/toolkit/sync/references/discovery.md`: the memory source. `reflect` and `correct`: the promotion step.
- `README.md`: a note that Engram is optional.

## Tests

- `mcp/engram.json` holds no secret or machine-specific path (gitleaks already covers `mcp/`).

## Acceptance criteria

- [ ] On a machine with Engram installed, setup wires it into the selected agents, and a second run changes nothing.
- [ ] `reflect` can cite a memory as evidence, without copying its content into a rule.

## Open questions

- Check Engram's current docs when implementing: the `--tools` profiles and the MCP command line.
