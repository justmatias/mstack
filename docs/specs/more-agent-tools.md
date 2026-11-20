# More agent tools

- **Phase:** future
- **Depends on:** `install-command` (installer targets), `install-manifest` (the rule renderer).

## Problem

mstack targets Claude Code and Cursor. Other agents read similar files: Codex CLI and others read `AGENTS.md`, Gemini CLI reads `GEMINI.md`, and GitHub Copilot reads `.github/copilot-instructions.md` in a repo. A machine that also uses one of them gets none of the rules or skills.

## Goal

Pluggable install targets, so adding a tool means adding one target definition. Start with Codex CLI, Gemini CLI and Copilot.

## Out of scope

- Tools without a file-based user or repo configuration.

## Design

- **Target interface:** each tool defines where skills go (if it supports skills), how rules are rendered (separate files, or one combined file with a managed block), and where they are written, per platform. Claude Code and Cursor become the first two targets, with no behavior change.
- **Renderers:** generalize `render-rule` from `install-manifest`: `separate-files` (Claude Code), `combined-block` (one `AGENTS.md` / `GEMINI.md` with `<!-- mstack:begin -->` … `<!-- mstack:end -->`, one section per rule), and `paste` (Cursor today).
- **Paths:** check each tool's current docs for user-level locations and skills support when implementing, and record the source in a comment in the target definition. Don't guess.
- **Copilot** is configured per repo. Its target is used by `mstack init --copilot` (writes or updates `.github/copilot-instructions.md` with the managed block) rather than by the user-level install.
- `--tool` accepts the new names, and `host-profiles` can list them.
- `discovery.md`'s tool-name mapping table gets a column per tool where skills are supported.

## Changes

- `src/mstack/install/targets/` (one module per tool), and refactoring the Claude Code and Cursor logic into it.
- `doctor`: per-target checks.
- `README.md` install table, and `discovery.md`.

## Tests

- Each target in a temporary `HOME`: paths, rendering, managed-block idempotency, and existing user text outside the block preserved.
- The existing Claude Code and Cursor tests pass unchanged after the refactor.

## Acceptance criteria

- [ ] `mstack install --tool codex` (and Gemini) installs the rules where the tool reads them, and a second run changes nothing.
- [ ] Adding a tool needs no change outside its target module and the docs.
