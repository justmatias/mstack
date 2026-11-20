# More agent tools

- **Phase:** future
- **Depends on:** nothing.

## Problem

mstack targets Claude Code and Cursor. Other agents read similar files: Codex CLI and opencode read `AGENTS.md`, Gemini CLI reads `GEMINI.md`, and GitHub Copilot reads `.github/copilot-instructions.md` in a repo. A machine that also uses one of them gets none of the rules or skills.

Skills are closer than they look. `.agents/skills/` is becoming the shared folder: Codex, Cursor and opencode all load it, as project skills (`.agents/skills/`) and as user skills (`~/.agents/skills/`). Claude Code is the exception and only loads `.claude/skills/` and `~/.claude/skills/`. Cursor and opencode also load the Claude Code folders for compatibility, and Codex does not.

## Goal

`setup-mstack` and `doctor` know where each tool reads skills and rules, so adding a tool means one row in the skill's table and one target definition for doctor. Start with Codex CLI, opencode, Gemini CLI and Copilot. Every tool the user picked loads every mstack skill exactly once.

## Out of scope

- Tools without a file-based user or repo configuration.

## Design

- **Setup:** the skill's "where things go" table gets a row per tool: where skills go (if it supports skills), how rules are written (separate files, or one combined file with a managed block), and where, per platform. The agent does the install; no installer code.
- **One shared skills copy:** `~/.agents/skills/` serves Codex, Cursor and opencode with a single copy. Claude Code still needs `~/.claude/skills/`. Choose the folders from the selected tools so that no tool loads a skill twice:
  - Claude Code alone: `~/.claude/skills/` (today's behavior).
  - Only `.agents` tools (Codex, Cursor, opencode in any mix): `~/.agents/skills/` only.
  - Claude Code with Cursor or opencode, without Codex: `~/.claude/skills/` only, since both load it too (today's "both").
  - Claude Code with Codex: Codex needs `~/.agents/skills/` and Claude Code needs `~/.claude/skills/`, so two copies, and Cursor or opencode on the same machine would then list each skill twice. See the open questions.
  - On WSL, a tool that runs on Windows (Cursor) reads the Windows profile, so its folder is in that home, as today.
- **Doctor targets:** each tool defines its folders and rule format, so doctor checks what is missing or drifted. Claude Code and Cursor become the first two targets, with no behavior change. The `duplicates` check generalizes: a skill reachable twice from one tool's folders is a warning, whichever two folders it is in.
- **Renderers:** generalize `render-rule`, so the setup and doctor agree on the installed text: `separate-files` (Claude Code), `combined-block` (one `AGENTS.md` / `GEMINI.md` with `<!-- mstack:begin -->` … `<!-- mstack:end -->`, one section per rule), and `paste` (Cursor today). Codex and opencode read a user-level `AGENTS.md` (the exact paths come from their docs, see below), so they take `combined-block`.
- **Paths:** check each tool's current docs for user-level locations and skills support when implementing, and record the source in a comment in the target definition. Don't guess.
- **Copilot** is configured per repo. Its target is used by `mstack init --copilot` (writes or updates `.github/copilot-instructions.md` with the managed block) rather than by the user-level install.
- `--tool` accepts the new names, as a list (`--tool claude,codex`) now that "both" no longer covers every mix, and `host-profiles` can list them.
- `discovery.md`'s tool-name mapping table gets a column per tool where skills are supported.

## Changes

- `src/mstack/doctor/targets.py` grows a definition per tool, and the folder choice above replaces `copied_folders`.
- `.agents/skills/setup-mstack/SKILL.md`: a row per tool, and the folder choice.
- `doctor`: per-target checks, the generalized `duplicates` check, and `--tool` as a list.
- `README.md` install table, and `discovery.md`.

## Tests

- Each target in a temporary `HOME`: doctor finds missing and drifted items, and renders each rule format.
- The folder choice for every mix of tools, and a skill in both `~/.agents/skills/` and `~/.claude/skills/` warns for a tool that loads both.
- The existing Claude Code and Cursor tests pass unchanged after the refactor.

## Docs

- `README.md`: the install table gets a row per tool.
- `.agents/skills/setup-mstack/SKILL.md`: the "where things go" table and the folder choice.
- `src/mstack/README.md`: the doctor groups and `--tool`.

## Acceptance criteria

- [ ] After `setup-mstack` with Codex, opencode (and Gemini), the skills and rules are where each tool reads them, and `mstack doctor --tool <tool>` is clean.
- [ ] With Codex, Cursor and opencode together, the skills are installed once, in `~/.agents/skills/`.
- [ ] No selected tool lists an mstack skill twice, or doctor warns about it.
- [ ] Adding a tool needs no change outside its target definition, the setup skill's table and the docs.

## Open questions

- Claude Code with Codex: accept that Cursor and opencode list each skill twice, or turn off their Claude Code compatibility folders where the tool allows it (opencode may have a setting for it; check before relying on it).
- Cursor's agent CLI: some reports say it missed `.agents/skills/`. Test the current version before choosing `~/.agents/skills/` for Cursor.
- Whether Gemini CLI and Copilot load `.agents/skills/` too, which would put them in the shared copy.
