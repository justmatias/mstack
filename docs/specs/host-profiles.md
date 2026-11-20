# Host profiles

- **Phase:** future
- **Depends on:** `install-command`. Better with `version-pinning` and `per-host-secrets`.

## Problem

The personal and work laptops should share most of the stack, but not all of it. The work machine may use only Claude Code, skip some skills or MCP servers, or need different settings. Today every machine installs everything, and the differences are kept by memory and by answering the same setup questions differently.

## Goal

Named profiles in the repo describe what a kind of machine gets. Each machine picks one profile and, if needed, adds a few local overrides. The same profile on two machines gives the same result.

## Out of scope

- Private overlay repos for work-only content (not planned yet).
- Secrets (`per-host-secrets`).

## Design

**Profiles in the repo**, generic and without domain details: `profiles/<name>.toml`.

```toml
# profiles/full.toml
tools = ["claude", "cursor"]
[include]
skills = ["*"]
rules = ["*"]
agents = ["*"]
mcp = []
```

```toml
# profiles/minimal.toml
tools = ["claude"]
[include]
skills = ["sync", "reflect"]
rules = ["error-handling", "logging", "git-commits"]
```

**Per machine:** `~/.config/mstack/config.toml` (never committed):

```toml
profile = "full"
version = "3.2.0"     # version-pinning
[overrides]
exclude = { mcp = ["<server>"] }
settings = { "statusLine.command" = "..." }
```

- Selection is by name, and `*` is a glob. Unknown names in a profile fail validation in CI.
- `mstack install` uses the profile's tools by default, and only installs what the profile includes. Items installed earlier but no longer included become `orphan`s (see `rollback-and-uninstall`).
- `mstack profile show` prints the resolved selection; `mstack profile use <name>` writes the machine config.

## Changes

- `profiles/`, a validator (part of `skills-check` or `config-check`), `src/mstack/profiles.py`, and install integration.
- `doctor`: shows the active profile, and warns when there is none.

## Tests

- Resolution: globs, overrides, unknown names. Install with each profile in a temporary `HOME`. A profile switch marks dropped items as orphans.

## Acceptance criteria

- [ ] Two machines with the same profile and version have identical installs (the same manifest hashes).
- [ ] Changing a machine's profile changes only what the profiles differ in.
