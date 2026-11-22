# Shared rule packs

- **Phase:** next
- **Depends on:** nothing open. Packs run through `mstack lint`, and repos choose them in `.mstack.toml` (`src/mstack/config.py`).

## Problem

mstack's checks (`no-bare-except`, `no-sleep-in-tests`, ...) only run inside this repo. To use them in a work repo, `sync` writes a copy into its `lint-rules/`. Copies don't get fixes, and the same check drifts across repos.

## Goal

A repo lists the packs it uses in `.mstack.toml`, and `mstack lint` runs mstack's versioned checks next to the repo's own, with per-repo overrides.

## Out of scope

- Third-party packs from other sources. The format allows it later.

## Design

**Packs in this repo:** `packs.toml` maps pack names to their prose rules and executable check IDs, so `rules/` and `lint/` keep their layout:

```toml
[packs.python-core]
rules = ["naming", "principles", "python-models", "python-modules"]
checks = ["no-bare-except", "no-isort-off", "no-manual-init-boilerplate", "no-module-docstring", "no-parent-relative-import", "no-swallowed-exception"]

[packs.testing]
rules = ["pytest-fixtures", "testing"]
checks = ["no-broad-pytest-raises", "no-fixture-in-test-module", "no-skip-without-reason", "no-sleep-in-tests", "no-underscore-fixture-parameter", "test-module-has-only-tests"]

[packs.git]
rules = ["git-commits"]
checks = []
```

The wheel includes `rules/`, `lint/rules/`, `lint/rule-tests/` and `packs.toml` as package data. An editable install reads them from the checkout.

**In a work repo:**

```toml
packs = ["python-core", "testing"]

[pack_overrides]
disable = ["no-manual-init-boilerplate"]
severity = { no-sleep-in-tests = "warning" }
```

**Host defaults:** users can select default packs once in their mstack user configuration. For example, `~/.config/mstack/config.toml` can set `packs = ["python-core", "testing"]`. When a repository has no `.mstack.toml`, mstack uses these defaults, so agent hooks run the shared checks in clean repositories without adding repo files. A repo's explicit `packs` setting replaces the host defaults, and its `[pack_overrides]` applies to the resulting selection. Host defaults configure local tools only. CI must select the packs in the repository config, or pass them explicitly to `mstack lint`, so CI behavior is reproducible and does not depend on a developer machine.

- `mstack lint` writes a temporary sgconfig whose `ruleDirs` are the repo's own plus each selected pack's rule files, with disabled rules removed and severities rewritten in the temporary copies. The repo's own rules win on an id clash, and the clash is logged.
- When no `.mstack.toml` exists, local commands resolve packs from the host defaults. An explicit repo `packs` list takes precedence; repo overrides still apply.
- `mstack coverage` resolves a pack check's optional `metadata.source` against the pack, and reports pack rules as such. A repo's prose rule can list a pack check with `enforced-by:`.
- **Prose for agents:** `setup-mstack` makes shared prose available in each agent's user settings, including Cursor User Rules. Shared prose stays out of consumer repositories. Coverage reads the original prose from the installed pack. Consumer repositories may still keep their own project-specific prose and checks.
- `mstack packs list` shows the available packs, their rules and checks.

## CI integration

The existing mstack composite action can run as a step in any GitHub Actions job. The caller checks out the consumer repo first, with full Git history for changed-file scans. A standalone `.github/workflows/mstack.yml` is an example. Teams can add the step to an existing workflow or run `mstack lint` directly with the pinned release on another CI platform.

Local tooling and CI use the same release for identical checks. Upgrading that release picks up changes in selected packs. Repositories can remove a pack or disable an individual check in `.mstack.toml`.

## Changes

- `packs.toml`, and package-data configuration.
- `src/mstack/packs.py`: loading, merging and overrides. Changes in `lint.py` and `check_rule_coverage.py`.
- A test that every rule in `rules/` belongs to exactly one pack.
- `sync`: when a repo rule matches a pack check, propose using the pack instead of copying it.

## Tests

- A temporary repo with `packs = ["python-core"]` and a violating file fails `mstack lint`; disabling the rule makes it pass; a severity override turns the error into a warning; a local rule with the same id wins.
- Coverage resolves pack sources.
- A clean CI runner can install a pinned mstack release and run a pack with only `.mstack.toml` in the consumer checkout.
- With host defaults configured, a clean repository without `.mstack.toml` gets those packs in agent hooks. A repo selection overrides the defaults.

## Docs

- `README.md`: "Use the checks in another repo" explains packs.
- `sync` and `authoring-a-check.md`: prefer a pack over a copy.

## Acceptance criteria

- [ ] A work repo gets mstack's checks with one line in `.mstack.toml`, with no copies of shared prose, checks or check tests.
- [ ] Upgrading mstack updates the checks in every repo that uses the pack.
- [ ] Overrides work without editing pack files.
- [ ] Users can set host-level default packs for agent-time checks in clean repositories, while CI remains explicitly configured per repository.
