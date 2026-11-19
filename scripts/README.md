# scripts

The tooling behind the `make` targets. ast-grep and import-linter check the code itself. These scripts cover what those tools cannot: keeping the prose rules and the checks in sync, validating exceptions, keeping domain details out of the rules, generating the rules table, picking the changed files, running the checks from agent hooks, and installing the integrations.

Scripts are grouped by purpose. Nothing is meant to be called directly: each one runs through the `make` target listed below. Python tools run as modules (`uv run python -m scripts.<folder>.<name>`) so they can import each other.

| Folder | What it holds | Run by |
| --- | --- | --- |
| `guards/` | Checks that fail the build when the rule system drifts. | `make guards` (part of `make lint-rules` and `make lint-rules-changed`) |
| `generate/` | Generators for files that must not be edited by hand. | `make rules-table` |
| `git/` | Helpers that read the git state. | `make lint-rules-changed` |
| `hooks/` | Agent hooks that scan each edited file and report findings back to the agent. | Claude Code / Cursor, once installed by `make setup` |

## guards/

- `check_rule_coverage.py`: every `.mdc` rule has a `## Checks` section, every check it lists exists, and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it.
- `check_exceptions.py`: every `# ast-grep-ignore` names its rules and carries a `# rule-exception:` with a reason, an expiry date that has not passed, and an approver.
- `check_no_domain_leak.py`: rules and checks contain no identifiers from the analyzed repo, and no URLs, emails or secrets.
- `conventions_inventory.py`: read-only inventory of the conventions store (name, tags, body hash); `check_rule_coverage.py` uses it to report personal rules whose source convention changed (`stale`) or was deleted (`orphan`).
- `generic_names.txt`: names and public hosts that `check_no_domain_leak.py` never reports.

## generate/

- `rules_table.py`: writes `docs/rules-table.md` (rule, check, severity, active exceptions) and updates the table between the `rules-table` markers in `CLAUDE.md` / `AGENTS.md`.

## git/

- `changed_files.sh`: lists the `.py` files changed relative to `origin/main` (`BASE_REF` overrides it), or the staged files with `--staged`.

## hooks/

- `claude_post_edit.sh`: Claude Code `PostToolUse` hook; on rule errors in the edited `.py` file, prints them to stderr and exits 2.
- `cursor_after_edit.sh`: Cursor `postToolUse` hook; returns the findings as `additional_context`.
- `lib.sh`: helpers shared by both hooks (read the edited path from the payload, scan one file).

## setup.py

- `setup.py`: the configurable setup CLI behind `make setup`. Installs or removes pre-commit, the agent hooks and the skills (`--help` lists the flags).
