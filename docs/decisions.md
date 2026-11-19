# Decisions

Decisions taken while executing `PLAN.md` that were not covered by `docs/design.md` or the plan, and adaptations of items marked **[VERIFY]**. Newest last.

| # | Phase | Decision | Reason |
| --- | --- | --- | --- |
| 1 | 0 | All tools are invoked as `uv run ast-grep ...`, never as `sg`. | On many Linux systems `sg` is the shadow-utils `setgroups` binary (it is on this machine: `/usr/bin/sg`). |
| 2 | 0 | `pre-commit` is a dev dependency managed by `uv`, not a global install. | `make setup` must work on a fresh machine with only `uv`. |
| 3 | 0 | `[tool.uv] package = false`: the repo is not an installable package; `example_app` is imported from the repo root. | Simplest option; `lint-imports` and `pytest` run from the root. |
| 4 | 1 | Verified the Cursor rule format: `.mdc` files under `.cursor/rules/` with `description`, `globs`, `alwaysApply` frontmatter (cursor.com/docs/context/rules). Unchanged from the plan. | [VERIFY] item. |
| 5 | 1 | `naming.mdc` has no file in `demo/violations/`. `domain_imports_infra.py` is not expected to produce an ast-grep finding; it is verified by the import-linter test instead. | Judgment rules have no deterministic check, and the architecture rule is enforced by import-linter, not ast-grep. |
| 6 | 1 | Dropped the `prefer-pydantic-over-dataclass` check and its demo file; `python-models.mdc` now prefers Pydantic but allows `@dataclass` when required. | PR #3 review: dataclasses should be allowed when required, not banned. |
