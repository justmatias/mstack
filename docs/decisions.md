# Decisions

Decisions taken while executing `PLAN.md` that were not covered by `docs/design.md` or the plan, and adaptations of items marked **[VERIFY]**. Newest last.

| # | Phase | Decision | Reason |
| --- | --- | --- | --- |
| 1 | 0 | All tools are invoked as `uv run ast-grep ...`, never as `sg`. | On many Linux systems `sg` is the shadow-utils `setgroups` binary (it is on this machine: `/usr/bin/sg`). |
| 2 | 0 | `pre-commit` is a dev dependency managed by `uv`, not a global install. | `make setup` must work on a fresh machine with only `uv`. |
| 3 | 0 | `[tool.uv] package = false`: the repo is not an installable package; `example_app` is imported from the repo root. | Simplest option; `lint-imports` and `pytest` run from the root. |
| 4 | 1 | Verified the Cursor rule format: `.mdc` files under `.cursor/rules/` with `description`, `globs`, `alwaysApply` frontmatter (cursor.com/docs/context/rules). Unchanged from the plan. | [VERIFY] item. |
| 5 | 1 | `naming.mdc` has no file in `demo/violations/`. `domain_imports_infra.py` is not expected to produce an ast-grep finding; it is verified by the import-linter test instead. | Judgment rules have no deterministic check, and the architecture rule is enforced by import-linter, not ast-grep. |
| 6 | 2 | Verified Python node names with `--debug-query`: a bare `except:` is an `except_clause` without a `value` field; `except Exception as e:` has `value: as_pattern`. ast-grep does not accept regex in `kind`, so "has a value" is written as `has: {field: value, regex: "."}`. | [VERIFY] item. |
| 7 | 2 | `ast-grep test` runs with `--skip-snapshot-tests`. Valid cases must not match and invalid cases must match; label snapshots are not stored. | Snapshots pin highlight ranges, not behavior, and every generated check would need a regenerated snapshot. Verified that a non-matching invalid case still fails. |
| 8 | 2 | `files`/`ignores` globs are matched against the path exactly as passed on the command line (relative to the cwd; absolute paths do not match `example_app/**`). Rules use `**/<folder>/**` globs so both relative and absolute paths (as sent by agent hooks) match. | Verified with ast-grep 0.51.3. |
| 9 | 2 | `no-print-in-app` is scoped to `**/example_app/**` and `**/demo/**`. | `demo/violations/print_debug.py` stands in for application code; without the second glob the demo could not show the rule. |
| 10 | 2 | `no-manual-init-boilerplate` ships as `warning` and is deliberately narrow: classes whose only method is `__init__`, whose `__init__` only contains `self.x = x` (and comments), and that do not subclass an `*Exception`/`*Error`. Broader detection (e.g. classes with other methods, `self.x = x` mixed with logic) is a Fixit candidate. | Dependency-injection constructors (`self.client = client` plus methods) are legitimate and very common; matching them would be a false positive. |
| 11 | 2 | The `domain_imports_infra.py` test copies `example_app/` and `.importlinter` into a pytest `tmp_path` and adds the demo file there, instead of writing into the real `example_app/domain/`. | Same check, without the risk of leaving a broken file in the working tree if the test is interrupted. |
