# `mstack init`

- **Phase:** now
- **Depends on:** `project-config` (writes `.mstack.toml`), `runtime-lint-command` (the scaffold calls `mstack lint`). Uses `pre-commit-hooks` and `reusable-ci-action` when they exist.

## Problem

Adopting rules-as-checks in a work repo is a manual recipe: "Adopting in a repo with no `lint-rules/`" in `authoring-a-check.md` tells the agent to create `sgconfig.yml` by hand, add dev dependencies, and then "propose the Makefile targets and CI job from the mstack README". Each repo ends up with a slightly different setup.

## Goal

`mstack init` scaffolds the same minimal, working layout in any repo, after showing what it will write.

## Out of scope

- Writing rules or checks (that is `sync-rules`).
- Modifying an existing layout. If the repo already has a sgconfig or `.mstack.toml`, init reports what exists and stops, except for the optional pieces that are still missing.

## Design

```text
mstack init [--rules-dir DIR] [--checks-dir DIR]
            [--pre-commit] [--ci github] [--makefile] [--dry-run] [--yes]
```

Always written:

- `.mstack.toml` with the chosen paths (defaults `.cursor/rules` and `lint-rules`).
- `<checks-dir>/sgconfig.yml`, plus empty `rules/` and `rule-tests/` folders (each with `.gitkeep`).
- `<rules-dir>/` if missing.

Optional:

- `--pre-commit`: appends the mstack hooks to `.pre-commit-config.yaml`, pinned to the installed version's tag (from `pre-commit-hooks`). Creates the file if missing.
- `--ci github`: writes `.github/workflows/mstack.yml` using the reusable action (from `reusable-ci-action`), with full and changed-files runs.
- `--makefile`: appends `lint-rules` and `lint-rules-changed` targets that call `mstack lint`, only if the targets don't exist.

Behavior:

- Prints the file list with `create` / `append` / `exists, skipped` and waits for confirmation, unless `--yes` is passed. `--dry-run` prints and exits.
- Never overwrites a file. Appends only to `.pre-commit-config.yaml` and `Makefile`, and only when the mstack entries aren't already there, so running it twice changes nothing.
- Templates live in `src/mstack/templates/` and are read with `importlib.resources`, so they ship in the wheel.
- After writing, runs `mstack lint` once and reports the result: an empty layout must pass.

## Changes

- Add `src/mstack/init.py` and `src/mstack/templates/` (`mstack.toml`, `sgconfig.yml`, `pre-commit.yaml`, `workflow.yml`, `Makefile.snippet`). Register `init` in `cli.py`.
- `authoring-a-check.md`: replace "Adopting in a repo with no `lint-rules/`" with "run `mstack init` and show the user its plan first".
- `sync-rules` step 1: if the repo has no checks layout, propose `mstack init`.

## Tests

- In a temporary git repo: a default init creates the expected tree, and `mstack lint` passes on it.
- A second run is a no-op.
- An existing `.pre-commit-config.yaml` gets the hooks appended with valid YAML, and the user's hooks are untouched.
- An existing Makefile target is skipped.
- `--dry-run` writes nothing.

## Docs

- `README.md`, "Use the skills in your projects": add `mstack init` as the first step in a new repo.
- `src/mstack/README.md`: the command.

## Acceptance criteria

- [ ] `mstack init --pre-commit --ci github` in an empty repo produces a layout where `mstack lint` and `pre-commit run --all-files` pass.
- [ ] Running it twice changes nothing.
- [ ] Nothing is written without confirmation unless `--yes` is passed.
