# Specs

Implementation plans for mstack. Each spec can be picked up on its own: it says what it depends on, what it changes, how it is tested and when it is done. Specs are combined only when one cannot ship without the other.

The goal behind all of them: set up the stack once per machine (personal laptop, work laptop) and keep the same skills, rules, checks and agent settings everywhere, with one command to verify it.

## Phases

### Next

| Spec | Summary | Depends on |
| --- | --- | --- |
| [pack-sources](pack-sources.md) | Load packs from any git repo or folder, pinned by a lockfile; the wheel ships no content | |
| [rulepack-extraction](rulepack-extraction.md) | Move the linter into its own tool, [rulepack](https://github.com/justmatias/rulepack), with its history | pack-sources, rulepack's [bootstrap](https://github.com/justmatias/rulepack/blob/main/docs/specs/bootstrap.md) |
| [mstack-uses-rulepack](mstack-uses-rulepack.md) | mstack keeps doctor and the stack tooling, deletes its linter copy, and runs `rulepack` everywhere | rulepack-extraction |

### Future

| Spec | Summary | Depends on |
| --- | --- | --- |
| [claude-code-plugin](claude-code-plugin.md) | Distribute skills, agents and hooks as a Claude Code plugin, for Claude Code-only machines | |
| [more-agent-tools](more-agent-tools.md) | Add opencode, Gemini CLI and GitHub Copilot targets | |
| [engram-memory](engram-memory.md) | Engram as an optional MCP memory server, feeding `reflect` | |

## Writing a spec

The "Depends on" column lists only specs that are still open: everything else they build on (`mstack lint`, `doctor`, `skills-check`, the `agents/`, `mcp/`, `settings/` and `instructions/` folders) already exists.

Every spec follows the same sections, so it can be implemented without reading the others:

- **Phase / Depends on**: hard dependencies must ship first; soft ones only add features when present.
- **Problem**: what is wrong or missing today, with file references.
- **Goal** and **Out of scope**.
- **Design**: the decisions, with the reason for each.
- **Changes**: the files to add, change or delete.
- **Tests**: what proves it works.
- **Docs**: which README, skill or reference must change in the same PR.
- **Acceptance criteria**: a checklist that closes the spec.
- **Open questions**: what to decide at implementation time.

When a spec ships, delete it in the same PR (git history keeps it) and remove its row here. A spec that changes phase only moves rows in this index.

Specs follow the repo principles too: English only, and practices, never domain details.
