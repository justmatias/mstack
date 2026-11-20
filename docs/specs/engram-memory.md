# Engram as the agent memory layer

- **Phase:** future
- **Depends on:** `agent-config-folders` (MCP and instructions), `doctor`. Better with `host-profiles` (personal and work memory kept apart) and `claude-code-plugin`.

## Problem

mstack keeps what should be **enforced** (rules and checks) and **how to work** (skills). It has no place for what agents **learn while working**: decisions, gotchas, how a project is laid out. Those stay in each tool's own memory, on each machine, and are lost between tools. [Engram](https://github.com/Gentleman-Programming/engram) (MIT) is a single binary that stores curated agent memories in local SQLite with full-text search. It exposes them over MCP to Claude Code, Cursor, Codex, Gemini CLI and others, and can export them to git (`engram sync`) for use on another machine.

## Goal

Engram becomes the optional memory layer of the stack: installed and verified the same way on every machine, wired into the agents mstack configures, and feeding `reflect`, so a learning that keeps coming back is promoted from memory to a rule with a check.

## Out of scope

- Replacing rules or skills with memories. A memory is a hint an agent may retrieve; a rule with a check is enforced. mstack's core idea stays the same.
- Hosting Engram Cloud.
- Vendoring Engram, or copying its skills or instructions into this repo without going through `integrate`.

## Design

**Layers, and what goes where:**

| Kind of knowledge | Lives in | Enforced |
| --- | --- | --- |
| A convention that can be checked | rule + check | yes, by `mstack lint` |
| A convention that needs judgment | rule with `llm-review` | in review |
| A workflow | skill | when invoked |
| A project fact, decision or gotcha | engram memory | no, retrieved on demand |

**Install and verify:**

- mstack doesn't install the binary. `doctor` checks that `engram` is on `PATH` and its version is at least the minimum (recorded in `mcp/engram.json`), and prints the official install command for the platform (Homebrew, `go install`, or a release archive).
- **Agent wiring:** prefer mstack's own `mcp/engram.json` (`engram mcp --tools=agent`), installed by `agent-config-folders`, so mstack's plan, backups and manifest cover it. Using `engram setup <agent>` is the alternative when its plugin or hooks are wanted; then mstack records that Engram owns that config and doesn't touch it. Never both for the same agent: `doctor` flags duplicate MCP entries.
- **Instructions:** a short section in `instructions/global.md` about when to save a memory (a decision, a non-obvious fix, a project convention not yet in a rule) and when to search one (at the start of a task in a known project). The same principles apply: English, and no secrets.

**Personal and work data stay apart:**

- Separate databases per profile, with `ENGRAM_DATA_DIR` set by the host profile (`host-profiles`), for example `~/.engram/personal` and `~/.engram/work`.
- `engram sync` exports into the **project repo's** `.engram/` folder, so work memories travel with work repos and personal ones with personal repos. mstack never syncs memories through its own repo, because they hold project details and this repo holds practices only.
- Prompts are not exported (Engram's default); the spec keeps it that way.

**Promotion into rules (`reflect`, `correct`):**

- New optional source in `discovery.md`: when the Engram MCP tools are available, search the current project's memories for corrections and conventions.
- A convention found in memories repeatedly counts as evidence, like a repeated correction in a transcript. It goes through the same principles (abstracted, no domain), and becomes a rule with a check. The reply suggests removing the memory once a rule covers it, so the two don't diverge.

## Changes

- `mcp/engram.json`, a section in `instructions/global.md`, a `doctor` check, an `ENGRAM_DATA_DIR` setting in the profiles.
- `skills/sync/references/discovery.md`: the memory source. `reflect` and `correct`: the promotion step.
- `README.md`: one row in "What's inside" and a note that Engram is optional.

## Tests

- `doctor` with and without `engram` on `PATH`, and with an old version.
- Install of `mcp/engram.json` in a temporary `HOME`, and duplicate detection when the agent's config already has an `engram` server.

## Acceptance criteria

- [ ] On a machine with Engram installed, setup wires it into the selected agents, and a second run changes nothing.
- [ ] Personal and work memories end up in different databases.
- [ ] `reflect` can cite a memory as evidence, without copying its content into a rule.

## Open questions

- Check Engram's current docs when implementing: the minimum version, the `--tools` profiles, and how `engram sync` merges chunks from two machines.
- Should Engram replace Claude Code's built-in memory, or run next to it? Recommendation: next to it at first; decide after a few weeks of use.
