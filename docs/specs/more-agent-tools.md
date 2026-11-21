# More agent tools

- **Phase:** future
- **Depends on:** nothing.

## Problem

Setup and doctor support Claude Code, Cursor and Codex. Users of opencode, Gemini CLI or GitHub Copilot still configure mstack rules and skills manually.

## Goal

Add the remaining tools to setup and doctor. Share user skill copies where the tools read the same folder.

## Out of scope

- Tools without file-based user or repository configuration.

## Design

- Verify each tool's current instructions and skill locations, including whether opencode reads a user-level `AGENTS.md` and where Gemini CLI reads `GEMINI.md`. Link the official sources in the target definitions.
- Extend setup and doctor with opencode and Gemini CLI targets. Reuse the managed-block renderer for global instruction files where supported.
- Reuse the existing `~/.agents/skills/` copy when another selected tool reads it. Extend duplicate warnings to the new tools' compatibility folders.
- Add `mstack init --copilot` to install or refresh a managed block in `.github/copilot-instructions.md`, preserving surrounding text.

## Changes

- Extend the setup skill's install table and doctor target selection.
- Add the Copilot option to `mstack init`.

## Tests

- Check each new doctor target with a temporary home containing missing, current and drifted installs.
- Cover mixed-tool folder choices and duplicate warnings for compatibility folders.
- Verify that running `mstack init --copilot` twice preserves text outside a single managed block.

## Docs

Update the install table, CLI reference and the sync skill's discovery reference for the new targets.

## Acceptance criteria

- [ ] Doctor checks opencode and Gemini CLI installs using their documented paths and formats.
- [ ] Tools with a shared skill location can use one installed copy, and doctor warns about copies a selected tool loads twice.
- [ ] `mstack init --copilot` installs and updates the repository's Copilot instructions block.

## Open questions

- Do Gemini CLI and Copilot read user skills from `~/.agents/skills/`?
- Can opencode disable compatibility folders when it can see two copies other tools need?
