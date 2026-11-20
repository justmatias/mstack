# Agent instructions

- The rules live in `rules/` (prose, source of truth), and their checks in `lint/`. Read the ones that match the files you touch before writing code.
- Before finishing, run `make lint-rules-changed` and fix every error it reports.
- Write everything in English, and never copy domain or business details into rules, checks or tests.

## Rules and what enforces them

<!-- rules-table:start -->
| Rule | Check | Enforced by | Severity | Active exceptions |
| --- | --- | --- | --- | --- |
| `rules/architecture-layers.mdc` | `domain-is-pure` | import-linter | error | 0 |
| `rules/error-handling.mdc` | `no-bare-except` | ast-grep | error | 0 |
| `rules/error-handling.mdc` | `no-swallowed-exception` | ast-grep | error | 0 |
| `rules/logging.mdc` | `no-print-in-app` | ast-grep | error | 0 |
| `rules/naming.mdc` | - | LLM review on the PR | comment only | - |
| `rules/python-models.mdc` | `no-manual-init-boilerplate` | ast-grep | warning | 0 |
<!-- rules-table:end -->
