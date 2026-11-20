# Runtime lint tools and `mstack lint`

- **Phase:** now
- **Depends on:** `project-config` (the command reads its paths from `.mstack.toml`).
- **Combines:** shipping the scan tools with the CLI, and the `mstack lint` command that runs them. The command cannot work without the tools.

## Problem

- `ast-grep-cli` and `import-linter` are dev dependencies (`pyproject.toml`), so `uv tool install` gives a global `mstack` that cannot run the checks. The skills then tell agents to run `uv run ast-grep ...`, which only works if the work repo installs ast-grep itself.
- The full flow (`ast-grep test`, `ast-grep scan`, `lint-imports`, `coverage`, `exceptions`, `leak-check`) only exists as the `lint-rules` and `lint-rules-changed` Makefile targets. A work repo has to copy the Makefile, and `authoring-a-check.md` step 9 lists the steps by hand for repos without it.
- Changed-file selection is a bash script (`scripts/git/changed_files.sh`) that only knows `*.py`.

## Goal

`mstack lint` runs the whole flow in any repo, with tools that come with the CLI. In this repo, `make lint-rules` becomes `uv run mstack lint`.

## Out of scope

- Hooks and CI wrappers (`pre-commit-hooks`, `reusable-ci-action`).
- Rule packs shipped with the CLI (`shared-rule-packs`).

## Design

Dependencies: move `ast-grep-cli` and `import-linter` to `[project].dependencies`. The ast-grep wheel ships its binary, so `uv tool install` puts it in the tool's environment. Resolve the binary next to `sys.executable` (the environment's scripts folder) before falling back to `PATH`, so the bundled version wins.

Command:

```text
mstack lint [--changed [--base-ref REF] [--staged]] [--files FILE ...]
            [--only STEP ...] [--skip STEP ...] [--json]
```

| Step | Runs | Skipped when |
| --- | --- | --- |
| `test` | `ast-grep test -c <sgconfig> --skip-snapshot-tests` | sgconfig has no `testConfigs` |
| `scan` | `ast-grep scan -c <sgconfig>` with the configured excludes | none |
| `imports` | `lint-imports` | no `.importlinter` |
| `coverage` | `check_rule_coverage` | no rules dir |
| `exceptions` | `check_exceptions` | none |
| `leak-check` | `check_no_domain_leak` over `[leak_check].paths` | no paths configured |

- **Modes.** The default scans everything, and warnings don't fail. `--changed` scans only the files changed against `base_ref` (or the staged files with `--staged`) and passes `--error`, as `lint-rules-changed` does today. `--files` scans exactly the given files with `--error` (used by pre-commit).
- **Changed files in Python.** Port `changed_files.sh` to `src/mstack/changed_files.py`, keeping its behavior: an explicit base ref that doesn't exist fails, the default falls back to local `main`, and untracked files are included. It filters by `[scan].extensions`, so shell files (`rule-pack-shell`) need no new script.
- **Steps run in order and all of them run**, even after a failure, so one run shows every problem. The exit code is non-zero if any step failed. `--json` prints `{step: {ok, findings}}` to stdout, and messages go to stderr through `logging` (`rules/logging.mdc`).
- **import-linter needs the project importable.** Prefer the project's own `lint-imports` when the repo's environment has one (`uv run --frozen lint-imports` when `uv.lock` lists import-linter). Otherwise run the bundled one with `PYTHONPATH` set to the repo root and `src/`. Log which one ran.
- **Guards are called in process** through their `main(argv)` functions, not through subprocesses.

## Changes

- `pyproject.toml`: move the two dependencies, then `uv lock`.
- Add `src/mstack/lint.py` (the step runner) and `src/mstack/changed_files.py`. Register `lint` in `cli.py`.
- `Makefile`: `lint-rules` becomes `uv run mstack lint`; `lint-rules-changed` becomes `uv run mstack lint --changed $(if $(STAGED),--staged)`; `guards` becomes `uv run mstack lint --only imports coverage exceptions leak-check`. Keep the target names, because `AGENTS.md`, CI and pre-commit use them.
- Delete `scripts/git/changed_files.sh`, `scripts/README.md` and `tests/scripts/` once nothing calls them. Update the README tables that mention `scripts/`.

## Tests

- `tests/mstack/test_changed_files.py`: a temporary git repo with a base branch; changed, untracked, deleted and renamed files; `--staged`; a missing explicit base ref fails; extension filtering.
- `tests/mstack/test_lint.py`: in a sandbox copy of `rules/`, `lint/` and `fixtures/`, a clean run passes; a file from `fixtures/invalid/` fails `scan`; `--changed` fails on a warning-level finding that the full scan tolerates; `--only` and `--skip`; a repo without `.importlinter` skips `imports`; `--json` output shape.
- A test asserts the bundled ast-grep is the one resolved.

## Docs

- `src/mstack/README.md`: the `lint` command and its steps.
- `authoring-a-check.md`: steps 4, 5 and 9 use `mstack lint --only test`, `--only scan` and `mstack lint`; drop the "run the steps directly" paragraph.
- `sync-rules` step 7, `correct-rules` (warnings scan): use `mstack lint`.
- `README.md`: "Working on mstack" lists the same `make` targets; mention that `mstack lint` works in any repo.

## Acceptance criteria

- [ ] After `uv tool install --editable .`, `mstack lint` works in a repo that has no Python dev dependencies.
- [ ] `make lint-rules`, `make lint-rules-changed` and `STAGED=1` behave as before, including warnings failing only on changed files.
- [ ] `scripts/git/changed_files.sh` is gone, and CI passes.

## Open questions

- Pin `ast-grep-cli` to a minor range (`>=0.x,<0.y`) so a new release can't silently change rule behavior? Recommendation: yes, with Dependabot raising updates.
