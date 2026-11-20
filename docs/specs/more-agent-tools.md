# More agent tools

- **Phase:** future
- **Depends on:** nothing.

## Problem

mstack targets Claude Code and Cursor. Other agents read similar files: Codex CLI and others read `AGENTS.md`, Gemini CLI reads `GEMINI.md`, and GitHub Copilot reads `.github/copilot-instructions.md` in a repo. A machine that also uses one of them gets none of the rules or skills.

## Goal

`setup-mstack` and `doctor` know where each tool reads skills and rules, so adding a tool means one row in the skill's table and one target definition for doctor. Start with Codex CLI, Gemini CLI and Copilot.

## Out of scope

- Tools without a file-based user or repo configuration.

## Design

- **Setup:** the skill's "where things go" table gets a row per tool: where skills go (if it supports skills), how rules are written (separate files, or one combined file with a managed block), and where, per platform. The agent does the install; no installer code.
- **Doctor targets:** each tool defines its folders and rule format, so doctor checks what is missing or drifted. Claude Code and Cursor become the first two targets, with no behavior change.
- **Renderers:** generalize `render-rule`, so the setup and doctor agree on the installed text: `separate-files` (Claude Code), `combined-block` (one `AGENTS.md` / `GEMINI.md` with `<!-- mstack:begin -->` … `<!-- mstack:end -->`, one section per rule), and `paste` (Cursor today).
- **Paths:** check each tool's current docs for user-level locations and skills support when implementing, and record the source in a comment in the target definition. Don't guess.
- **Copilot** is configured per repo. Its target is used by `mstack init --copilot` (writes or updates `.github/copilot-instructions.md` with the managed block) rather than by the user-level install.
- `--tool` accepts the new names, and `host-profiles` can list them.
- `discovery.md`'s tool-name mapping table gets a column per tool where skills are supported.

## Changes

- `src/mstack/doctor/targets.py` grows a definition per tool.
- `.claude/skills/setup-mstack/SKILL.md`: a row per tool.
- `doctor`: per-target checks.
- `README.md` install table, and `discovery.md`.

## Tests

- Each target in a temporary `HOME`: doctor finds missing and drifted items, and renders each rule format.
- The existing Claude Code and Cursor tests pass unchanged after the refactor.

## Acceptance criteria

- [ ] After `setup-mstack` with Codex (and Gemini), the rules are where the tool reads them, and `mstack doctor --tool codex` is clean.
- [ ] Adding a tool needs no change outside its target definition, the setup skill's table and the docs.
