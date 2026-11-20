# `mstack doctor`

- **Phase:** now
- **Depends on:** `install-manifest` (soft: drift checks only when the manifest exists), `skill-validation` (soft: reuses its validator).

## Problem

On a new or second machine there is no quick way to tell whether the stack is complete. This laptop is an example: `mstack` was not on `PATH`, `~/.claude/rules/` did not exist and no mstack skill was installed, and nothing said so. The skills only find out halfway through a task, when `mstack` is not found.

## Goal

One command that says whether this machine is set up like the others, what is missing, and how to fix each problem.

## Out of scope

- Fixing anything. Doctor only reports, and prints the command that fixes each problem.
- Network checks by default.

## Design

```text
mstack doctor [--tool claude|cursor|both] [--online] [--json]
```

`--tool` defaults to the tools whose folders exist. Checks are grouped, and each one returns `ok`, `warn` or `error` with a one-line fix:

| Group | Check | Fix shown |
| --- | --- | --- |
| tools | `uv`, `git` on `PATH`; `gh` (warn only: `correct-rules` and `integrate-skills` use it) | install link |
| cli | `mstack` on `PATH` and the same version as the running one; the bundled ast-grep runs | `uv tool install --editable <checkout>` |
| source | the checkout path the CLI was installed from exists and is a git repo; uncommitted changes (warn) | none |
| skills | every mstack skill is installed in the selected tool's folder; each passes `skills-check --profile generic`; no skill exists in both `~/.claude/skills/` and `~/.cursor/skills/` | run `setup-mstack` |
| rules | every mstack rule is installed in `~/.claude/rules/` with no frontmatter | run `setup-mstack` |
| drift | manifest states other than `identical` (from `mstack manifest status`) | run `setup-mstack` |
| platform | WSL with Cursor on Windows: the skills folder Cursor reads is on the Windows side (see `portability`) | path to use |
| version | `--online`: the latest release tag is newer than the installed version | `git pull`, then `setup-mstack` |

- Exit code: 1 if any `error`, otherwise 0. `--json` prints the full report to stdout, and the human table goes to stderr.
- `--online` uses `git ls-remote --tags` on the source checkout's `origin`, so it needs no GitHub token.
- Every check is a small function with the same signature, registered in a list. Adding a check means adding one function.

## Changes

- Add `src/mstack/doctor/` (a check registry and one module per group) and register `doctor` in `cli.py`.
- `setup-mstack` step 8 ends with `mstack doctor` instead of its manual list (keep only what doctor cannot check).

## Tests

- Each check against a temporary `HOME`: a missing folder, a duplicate skill, a broken skill, a rule with frontmatter, every drift state.
- Tools missing from `PATH` (patched `shutil.which`).
- `--json` output shape and exit codes.
- `--online` with a local bare repo as `origin`.

## Docs

- `README.md`, "Getting started": a new last step, "Verify: `mstack doctor`".
- `src/mstack/README.md`: the command.

## Acceptance criteria

- [ ] On a machine with nothing installed, doctor lists every missing piece with its fix, and exits 1.
- [ ] After `setup-mstack`, doctor exits 0.
- [ ] No network access without `--online`.
