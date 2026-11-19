# Agent instructions

- The team's rules live in `.cursor/rules/` (prose, source of truth). Read the ones that match the files you touch before writing code.
- Before finishing, run `make lint-rules-changed` and fix every error it reports.
- Write everything in English, and never copy domain or business details into rules, checks or tests.

## Rules and what enforces them

<!-- rules-table:start -->
| Rule | Check | Enforced by | Severity | Active exceptions |
| --- | --- | --- | --- | --- |
| `.cursor/rules/architecture-layers.mdc` | `domain-is-pure` | import-linter | error | 0 |
| `.cursor/rules/error-handling.mdc` | `no-bare-except` | ast-grep | error | 0 |
| `.cursor/rules/error-handling.mdc` | `no-swallowed-exception` | ast-grep | error | 0 |
| `.cursor/rules/logging.mdc` | `no-print-in-app` | ast-grep | error | 0 |
| `.cursor/rules/naming.mdc` | - | LLM review on the PR | comment only | - |
| `.cursor/rules/python-models.mdc` | `no-manual-init-boilerplate` | ast-grep | warning | 0 |
| `.cursor/rules/python-models.mdc` | `prefer-pydantic-over-dataclass` | ast-grep | error | 0 |
<!-- rules-table:end -->
