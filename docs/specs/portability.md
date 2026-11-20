# Portability: Linux, macOS, Windows and WSL

- **Phase:** now
- **Depends on:** `runtime-lint-command` (soft: it replaces the bash changed-files script with Python).

## Problem

The stack is meant to work the same on every machine, but it assumes one environment:

- **WSL and Cursor.** Cursor running on Windows reads `%USERPROFILE%\.cursor` (from WSL, `/mnt/c/Users/<user>/.cursor`), not `~/.cursor` inside WSL. `setup-mstack` installs to the WSL home, where Windows Cursor never looks. Claude Code inside WSL uses the WSL home, so the two tools need different targets on the same laptop.
- **Bash and GNU tools.** The Makefile sets `SHELL := /usr/bin/env bash` and uses `<<<`; `scripts/git/changed_files.sh` is bash. Native Windows has neither, and macOS ships bash 3.2.
- **Paths.** The skills write `~/.claude/...` in prose and assume `/`. Backups use `cp -R` and `mv`.
- **Line endings.** There is no `.gitattributes`, so a Windows checkout with `core.autocrlf=true` turns shell scripts and fixture files into CRLF, which breaks bash and can change ast-grep results.
- **CI** runs on `ubuntu-latest` only.

## Goal

The CLI, the checks and the setup behave the same on Linux, macOS, native Windows and WSL, and CI proves it.

## Out of scope

- Supporting `make` on native Windows. The CLI is the portable entry point; `make` stays a contributor convenience.

## Design

1. **Detect the platform once:** `src/mstack/platform.py` returns `linux`, `macos`, `windows` or `wsl` (WSL when `/proc/version` contains `microsoft`), and the user-level folders for each tool as `pathlib.Path`s, from `Path.home()` and `%USERPROFILE%`.
2. **WSL targets:** on WSL, Claude Code targets the WSL home. Cursor targets the Windows profile, found with `wslpath "$(cmd.exe /c echo %USERPROFILE% 2>/dev/null)"`, or the `MSTACK_WINDOWS_HOME` environment variable when that fails. `setup-mstack` says which home each tool uses before planning. Because the tools live in different homes on WSL, "both" means two copies, not one.
3. **No shell in the CLI path:** everything the CLI runs is Python plus `git` and the bundled ast-grep. The changed-files script is ported by `runtime-lint-command`. If that hasn't landed, port it here.
4. **Line endings:** add `.gitattributes` with `* text=auto eol=lf`, and `*.bat` / `*.cmd` as `eol=crlf` if any are added.
5. **File operations in skills:** `setup-mstack` keeps shell commands as examples, but says that on native Windows the agent uses PowerShell equivalents (`Copy-Item -Recurse`, `Move-Item`), or the CLI commands once `install-command` exists.
6. **CI matrix:** add `macos-latest` and `windows-latest` to a `portability` job that runs `make test`'s pytest directly (`uv run pytest -q`) and `uv run mstack lint`. The existing Linux job stays as is.

## Changes

- `src/mstack/platform.py` and tests.
- `skills/setup-mstack/SKILL.md` step 1: show the resolved home per tool, and the WSL case. `sync-rules/references/discovery.md`: the Cursor user folder note for WSL.
- `doctor`'s `platform` check uses `platform.py`.
- `.gitattributes`.
- `.github/workflows/ci.yml`: the `portability` job.
- Fix whatever the new CI jobs find: `/`-joined path strings in guards and tests, `subprocess` calls that assume a POSIX shell, `encoding="utf-8"` missing in reads and writes.

## Tests

- `platform.py` with patched `/proc/version`, `sys.platform` and environment variables, for each platform and the WSL fallbacks.
- The full test suite on the three operating systems in CI.

## Docs

- `README.md`, "Getting started": a short "Windows and WSL" note on where each tool's files go.

## Acceptance criteria

- [ ] CI passes on Linux, macOS and Windows.
- [ ] On WSL, `setup-mstack` installs Cursor skills where Windows Cursor reads them, and Claude Code skills in the WSL home.
- [ ] A Windows checkout keeps LF line endings in scripts and fixtures.
