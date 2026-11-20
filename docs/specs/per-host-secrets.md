# Per-host secrets and values

- **Phase:** future
- **Depends on:** nothing open. The `${VAR}` placeholders live in `mcp/` and `settings/`. Better with `host-profiles`.

## Problem

MCP servers and some settings need tokens, URLs or account names that differ between machines and must never reach the repo. `mcp/` and `settings/` only allow `${VAR}` placeholders, so something has to supply the values on each machine, and say clearly when one is missing.

## Goal

Placeholders are resolved per machine at install time, or left for the tool to expand at runtime, and the values stay out of the repo and out of mstack's own files.

## Out of scope

- Managing secrets for projects or CI.

## Design

- **Prefer runtime expansion.** If the target tool expands environment variables in its config (check which Claude Code and Cursor config files support `${VAR}` when implementing), install the placeholder unchanged, and only check the variable is set. The secret then never lands in a config file.
- **Otherwise resolve at install time**, in this order:
  1. the process environment;
  2. `~/.config/mstack/secrets.env` (`KEY=value` lines; created with mode `0600`; doctor warns if it is group- or world-readable);
  3. the OS keychain through the optional `keyring` extra (`uv tool install 'mstack[keyring]'`);
  4. an interactive prompt, which offers to save to 2 or 3.
- **Never written** to backups' logs or to command output. The plan shows `${VAR} → set` or `missing`, never the value.
- **Non-secret per-host values** (an editor path, a default model) use the same mechanism, so there's one way to customize a machine.
- `mstack secrets list` shows each placeholder in the installed items and whether it is resolved, without the values.

## Changes

- `src/mstack/secrets.py`, install integration, and `mstack secrets list`.
- `doctor`: unresolved placeholders and file permissions.
- `mcp/README.md` and `settings/README.md`: how to declare a placeholder.

## Tests

- Resolution order, prompt saving, `0600` creation, no value in any output or log (capture and search), and runtime-expansion targets left untouched.

## Acceptance criteria

- [ ] An MCP server that needs a token installs on two machines with different tokens from the same repo file.
- [ ] No secret value appears in the repo, backups metadata or command output.
