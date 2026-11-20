# Specs

Implementation plans for mstack. Each spec can be picked up on its own: it says what it depends on, what it changes, how it is tested and when it is done. Specs are combined only when one cannot ship without the other.

The goal behind all of them: set up the stack once per machine (personal laptop, work laptop) and keep the same skills, rules, checks and agent settings everywhere, with one command to verify it.

## Phases

### Now

Suggested order: `runtime-lint-command` first; it unblocks most of the rest.

| Spec | Summary | Depends on |
| --- | --- | --- |

### Next

| Spec | Summary | Depends on |
| --- | --- | --- |
| [agent-hooks](agent-hooks.md) | Agent hooks that run the checks while the agent edits | agent-config-folders, runtime-lint-command |
| [shared-rule-packs](shared-rule-packs.md) | Repos consume mstack's checks instead of copying the YAML | runtime-lint-command |

### Future

| Spec | Summary | Depends on |
| --- | --- | --- |
| [claude-code-plugin](claude-code-plugin.md) | Distribute skills, agents and hooks as a Claude Code plugin | agent-config-folders, skill-validation |
| [host-profiles](host-profiles.md) | Per-machine profiles (personal, work) choosing what gets installed | |
| [per-host-secrets](per-host-secrets.md) | `${VAR}` placeholders resolved per machine, never stored in the repo | agent-config-folders |
| [more-agent-tools](more-agent-tools.md) | Codex, Gemini CLI and Copilot targets | |
| [engram-memory](engram-memory.md) | Engram as the optional, per-profile agent memory layer, feeding `reflect` | agent-config-folders, doctor |

## Writing a spec

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
