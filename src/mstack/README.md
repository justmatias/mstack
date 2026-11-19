# mstack (package)

The `mstack` command: the guards and generators that `make lint-rules` and the skills run. Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack coverage` | `guards/check_rule_coverage.py` | Every `.mdc` rule has a `## Checks` section, every check it lists exists, and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it. |
| `mstack exceptions` | `guards/check_exceptions.py` | Every `# ast-grep-ignore` names its rules and carries a `# rule-exception:` with a reason, an expiry date that has not passed, and an approver. |
| `mstack leak-check` | `guards/check_no_domain_leak.py` | Rules and checks contain no identifiers from the analyzed repo, and no URLs, emails or secrets. `guards/generic_names.txt` lists names and public hosts it never reports. Known gap: single-word function names (`refund()`, `reconcile()`) are not collected, to avoid false positives on generic verbs. |
| `mstack rules-table` | `generate/rules_table.py` | Writes `docs/rules-table.md` and updates the table between the `rules-table` markers in `CLAUDE.md` / `AGENTS.md`. |

Data output (JSON, inventories) goes to stdout; messages go to stderr through `logging`, as `.cursor/rules/logging.mdc` asks.
