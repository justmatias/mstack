# Host profiles

- **Phase:** future
- **Depends on:** nothing. Better with `per-host-secrets`.

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
rules = ["error-handling", "git-commits"]
```

**Per machine:** `~/.config/mstack/config.toml` (never committed):

```toml
profile = "full"
[overrides]
exclude = { mcp = ["<server>"] }
settings = { "statusLine.command" = "..." }
```

- Selection is by name, and `*` is a glob. Unknown names in a profile fail validation in CI.
- `setup-mstack` reads the machine config: it uses the profile's tools instead of asking, installs only what the profile includes, and offers to remove (with a backup) mstack items installed earlier that the profile no longer includes.
- `mstack profile show` prints the resolved selection, so the skill and `doctor` read the same answer; `mstack profile use <name>` writes the machine config.

## Changes

- `profiles/`, a validator (part of `skills-check`, or its own guard), and `src/mstack/profiles.py`.
- `setup-mstack`: a step that reads the profile.
- `doctor`: shows the active profile, warns when there is none, and checks only the profile's items.

## Tests

- Resolution: globs, overrides, unknown names. `doctor` in a temporary `HOME` reports only the profile's items as missing.

## Acceptance criteria

- [ ] Two machines with the same profile and checkout get the same items, and `doctor` shows no drift on either.
- [ ] Changing a machine's profile changes only what the profiles differ in.
