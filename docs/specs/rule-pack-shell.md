# Rule pack: shell scripts

- **Phase:** now
- **Depends on:** `hook-checks` (shellcheck runs as a hook). Better with `runtime-lint-command`, whose changed-files selection reads `[scan].extensions`; without it, extend `scripts/git/changed_files.sh` to `*.sh`.

## Problem

Every rule today is about Python. Agents write shell scripts often (setup scripts, CI steps, hooks), and the common mistakes are known and checkable: no strict mode, unquoted expansions, backticks, `eval`.

## Goal

A `rules/shell.mdc` rule with checks, fixtures and tests, following the same conventions as the Python rules.

## Out of scope

- POSIX `sh` portability rules. The rule targets bash, which the repo already uses (`#!/usr/bin/env bash`).
- Formatting (shfmt). Can be a later hook.

## Design

`rules/shell.mdc`, `globs: "**/*.sh"`:

| Bullet | Check | Tool |
| --- | --- | --- |
| Start with `#!/usr/bin/env bash` | `enforced-by-hook: shellcheck` (SC2148 catches a missing shebang); the exact form is judgment | shellcheck |
| Enable strict mode right after the shebang: `set -euo pipefail` | `shell-strict-mode` | ast-grep (`language: bash`): a `program` with no `command` matching `set -euo pipefail` (or `set -Eeuo pipefail`) |
| Quote every expansion: `"$var"`, `"$(cmd)"` | `enforced-by-hook: shellcheck` (SC2086 and related) | shellcheck |
| Use `$(...)`, never backticks | `no-backtick-substitution` | ast-grep: `command_substitution` whose text starts with a backtick |
| Never use `eval` | `no-eval` | ast-grep: `command` whose name is `eval` |
| Send errors to stderr (`>&2`) and exit non-zero | judgment | `enforcement: llm-review` |

Verify every node kind with `ast-grep run -l bash -p '<snippet>' --debug-query=ast` before writing the YAML, as `authoring-a-check.md` asks.

Severity: `error` for checks with zero violations in the repo when added (measure first, per step 5 of the recipe).

## Changes

- `rules/shell.mdc`.
- `lint/rules/shell-strict-mode.yml`, `no-backtick-substitution.yml`, `no-eval.yml`, each with `metadata.source: rules/shell.mdc`.
- `lint/rule-tests/<id>-test.yml`, each with at least 2 valid (including near misses: `set -euo pipefail` after comments, a string containing a backtick, a function named `evaluate`) and 2 invalid cases.
- `fixtures/valid/scripts/example.sh` and `fixtures/invalid/shell/<one file per check>.sh`.
- `tests/test_checks.py`: build the invalid file list from every file in `fixtures/invalid/`, not only `*.py`.
- `.pre-commit-config.yaml`: add `shellcheck` (for example the `shellcheck-py` mirror), pinned and with `hookpin` passing.
- `src/mstack/guards/check_exceptions.py`: today it tokenizes Python only. Extend it to `.sh` files with line-based `#` comment parsing, so `# ast-grep-ignore` in shell also needs a `# rule-exception:`. Add tests.
- `[scan].extensions` (or `changed_files.sh`) includes `.sh`.

## Tests

- `ast-grep test` for the three rules.
- `test_every_invalid_fixture_is_caught` covers the shell fixtures.
- `test_valid_fixtures_have_no_errors` covers `example.sh`.
- Exceptions guard tests for a shell file with and without `rule-exception`.

## Docs

- `README.md`: nothing beyond the generic tables, unless a "rules" list is reintroduced.
- `authoring-a-check.md`: one example of a bash pattern next to the Python facts.

## Acceptance criteria

- [ ] `make lint-rules`, `make demo` and `make test` pass, and the demo fails on every shell fixture.
- [ ] `mstack coverage` resolves both the ast-grep checks and the shellcheck hook.
- [ ] `mstack leak-check` passes on the new rule and checks.
