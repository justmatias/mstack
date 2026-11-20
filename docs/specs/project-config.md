# Project config (`.mstack.toml`)

- **Phase:** now
- **Depends on:** none. Unblocks `runtime-lint-command`, `init-command`, `shared-rule-packs`.

## Problem

The guards default to a work repo's layout (`.cursor/rules/`, `lint-rules/sgconfig.yml`, `.importlinter`), while this repo uses `rules/` and `lint/`. Every caller passes the paths again:

- `Makefile` defines `RULE_PATHS := --rules-dir rules --config $(SGCONFIG)`, the scan excludes, and a long `leak-check ... --exclude ...` line.
- `tests/mstack/guards/conftest.py` repeats them in `coverage_arguments`.
- The skills hard-code `.cursor/rules/` and `lint-rules/` in prose (`sync-rules`, `correct-rules`, `authoring-a-check.md`, `discovery.md`).

A repo with another layout has to repeat its paths on every command, and an agent can easily pass the wrong ones.

## Goal

One optional file at the repo root describes the layout. Every `mstack` command reads it, and flags still override it.

## Out of scope

- User or host settings (see `host-profiles`).
- Rule packs (see `shared-rule-packs`), although the schema leaves room for a `packs` key.

## Design

File: `.mstack.toml` at the git root. Fallback: a `[tool.mstack]` table in `pyproject.toml`, for Python repos that prefer one file. If both exist, `.mstack.toml` wins and the command logs a warning.

```toml
rules_dir = ".cursor/rules"          # prose rules (*.mdc)
sgconfig = "lint-rules/sgconfig.yml" # ast-grep config
importlinter = ".importlinter"       # optional; skipped when missing

[scan]
exclude = ["fixtures/invalid/**"]    # globs passed to ast-grep scan
extensions = [".py"]                 # what --changed considers

[leak_check]
paths = ["lint-rules", ".cursor/rules"]
exclude = []                         # tooling folders that are not analyzed code

[changed]
base_ref = "origin/main"
```

- **Discovery:** walk up from the current directory to the git root and stop there. Never read a config above the repo.
- **Precedence:** CLI flag, then config file, then built-in defaults (the current ones, so repos without the file behave exactly as today).
- **Paths** are relative to the file's directory, so commands work from any subfolder.
- **Model:** a `pydantic.BaseModel` with `extra="forbid"`, following `rules/python-models.mdc`, so a typo in a key fails loudly. This adds `pydantic` to the runtime dependencies (today it is dev-only, for `fixtures/valid/`).
- **Parsing:** `tomllib` from the standard library (Python 3.12+).
- **Command:** `mstack config` prints the resolved config with the source of each value (default, file or flag), and `mstack config --json` prints it as JSON.

## Changes

- Add `src/mstack/config.py` with the model, discovery and merge logic.
- Change `check_rule_coverage.main`, `check_exceptions.main` and `check_no_domain_leak.main` to take their defaults from the resolved config. `leak-check` keeps its positional `paths` and uses `[leak_check].paths` when none are given. `--repo` defaults to the git root.
- Register `config` in `src/mstack/cli.py`.
- Add `.mstack.toml` to this repo with `rules_dir = "rules"`, `sgconfig = "lint/sgconfig.yml"`, the scan exclude and the leak-check paths and excludes now in the Makefile.
- In the `Makefile`, drop `RULE_PATHS`, `SCAN_EXCLUDES` and the leak-check flags. The targets call the commands without paths.

## Tests

- `tests/mstack/test_config.py`: defaults with no file; `.mstack.toml` only; `[tool.mstack]` only; both, where `.mstack.toml` wins with a warning; unknown key fails; a flag overrides the file; discovery from a subfolder; discovery stops at the git root.
- Existing guard tests pass with `coverage_arguments` removed, because the repo's own `.mstack.toml` supplies the paths.

## Docs

- `src/mstack/README.md`: a "Configuration" section with the schema.
- `skills/sync-rules/references/discovery.md`: the rules and checks may live where `.mstack.toml` says; run `mstack config` to find them.
- `authoring-a-check.md`, `sync-rules`, `correct-rules`: replace the hard-coded `lint-rules/...` paths with "the configured sgconfig (default `lint-rules/sgconfig.yml`)".

## Acceptance criteria

- [ ] `mstack coverage`, `mstack exceptions` and `mstack leak-check` run in this repo with no path flags.
- [ ] A repo without `.mstack.toml` gets today's defaults.
- [ ] `mstack config` shows where each value came from.
- [ ] `make lint-rules` and `make test` pass.

## Open questions

- Should `mstack config --init` write a commented default file, or is that `mstack init`'s job? Recommendation: `mstack init` only.
