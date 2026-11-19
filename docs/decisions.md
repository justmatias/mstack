# Decisions

Decisions taken while executing `PLAN.md` that were not covered by `docs/design.md` or the plan, and adaptations of items marked **[VERIFY]**. Newest last.

| # | Phase | Decision | Reason |
| --- | --- | --- | --- |
| 1 | 0 | All tools are invoked as `uv run ast-grep ...`, never as `sg`. | On many Linux systems `sg` is the shadow-utils `setgroups` binary (it is on this machine: `/usr/bin/sg`). |
| 2 | 0 | `pre-commit` is a dev dependency managed by `uv`, not a global install. | `make setup` must work on a fresh machine with only `uv`. |
| 3 | 0 | `[tool.uv] package = false`: the repo is not an installable package; `example_app` is imported from the repo root. | Simplest option; `lint-imports` and `pytest` run from the root. |
