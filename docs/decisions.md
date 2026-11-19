# Decisions

Decisions taken while executing `PLAN.md` that were not covered by `docs/design.md` or the plan, and adaptations of items marked **[VERIFY]**. Newest last.

| # | Phase | Decision | Reason |
| --- | --- | --- | --- |
| 1 | 0 | All tools are invoked as `uv run ast-grep ...`, never as `sg`. | On many Linux systems `sg` is the shadow-utils `setgroups` binary (it is on this machine: `/usr/bin/sg`). |
| 2 | 0 | `pre-commit` is a dev dependency managed by `uv`, not a global install. | `make setup` must work on a fresh machine with only `uv`. |
| 3 | 0 | `[tool.uv] package = false`: the repo is not an installable package; the fixture code (`fixtures.valid`) is imported from the repo root. | Simplest option; `lint-imports` and `pytest` run from the root. |
| 4 | 1 | Verified the Cursor rule format: `.mdc` files under `.cursor/rules/` with `description`, `globs`, `alwaysApply` frontmatter (cursor.com/docs/context/rules). Unchanged from the plan. | [VERIFY] item. |
| 5 | 1 | `naming.mdc` has no folder in `fixtures/invalid/`. `domain_imports_infra.py` is not expected to produce an ast-grep finding; it is verified by the import-linter test instead. | Judgment rules have no deterministic check, and the architecture rule is enforced by import-linter, not ast-grep. |
| 6 | 1 | Dropped the `prefer-pydantic-over-dataclass` check and its invalid fixture; `python-models.mdc` now prefers Pydantic but allows `@dataclass` when required. | PR #3 review: dataclasses should be allowed when required, not banned. |
| 7 | 1 | Fixtures live under one `fixtures/` folder: `fixtures/valid/` (was `example_app/`, must pass every check) and `fixtures/invalid/<rule>/` (was `demo/violations/`, one folder per `.mdc` rule, must be caught). Kept in this repo, not a submodule. `make demo` keeps its name. | PR #3 review: one folder for all fixtures. `valid`/`invalid` matches ast-grep's rule-test keys; `pass` is a Python keyword and could not be imported. A submodule would split every rule change across two repos. The folder layout replaces the file-to-rule table. |
