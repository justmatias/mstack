# Shared rule packs

- **Phase:** next
- **Depends on:** `runtime-lint-command` (packs run through `mstack lint`); repos choose packs in `.mstack.toml` (`src/mstack/config.py`).

## Problem

mstack's checks (`no-bare-except`, `no-print-in-app`, ...) only run inside this repo. To use them in a work repo, `sync` writes a copy into its `lint-rules/`. Copies don't get fixes, and the same check drifts across repos.

## Goal

A repo lists the packs it uses in `.mstack.toml`, and `mstack lint` runs mstack's versioned checks next to the repo's own, with per-repo overrides.

## Out of scope

- Third-party packs from other sources. The format allows it later.

## Design

**Packs in this repo:** `packs.toml` maps pack names to the rules they contain, so `rules/` and `lint/` keep their layout:

```toml
[packs.python-core]
rules = ["error-handling", "logging", "python-models", "naming"]

[packs.testing]
rules = ["testing"]

[packs.shell]
rules = ["shell"]
```

The wheel includes `rules/`, `lint/rules/`, `lint/rule-tests/` and `packs.toml` as package data (see `packaged-install` for the build details; an editable install reads them from the checkout).

**In a work repo:**

```toml
packs = ["python-core", "testing"]

[packs.overrides]
disable = ["no-manual-init-boilerplate"]
severity = { no-print-in-app = "warning" }
```

- `mstack lint` writes a temporary sgconfig whose `ruleDirs` are the repo's own plus each selected pack's rule files, with disabled rules removed and severities rewritten in the temporary copies. The repo's own rules win on an id clash, and the clash is logged.
- `mstack coverage` resolves a pack check's `metadata.source` against the pack, and reports pack rules as such. A repo's prose rule can list a pack check with `enforced-by:`.
- **Prose for agents:** the pack's `.mdc` files are already installed as user rules by `setup-mstack`. Optionally, `mstack packs export --to .cursor/rules/mstack/` writes them into the repo for teammates without mstack, with a header saying they are generated and which version they came from. `mstack lint` warns when an exported copy is stale.
- `mstack packs list` shows the available packs, their rules and checks.

## Changes

- `packs.toml`, and package-data configuration.
- `src/mstack/packs.py`: loading, merging, overrides, export. Changes in `lint.py` and `check_rule_coverage.py`.
- A test that every rule in `rules/` belongs to exactly one pack.
- `sync`: when a repo rule matches a pack check, propose using the pack instead of copying it.

## Tests

- A temporary repo with `packs = ["python-core"]` and a violating file fails `mstack lint`; disabling the rule makes it pass; a severity override turns the error into a warning; a local rule with the same id wins.
- Coverage resolves pack sources.
- Export writes the files with the header, and the staleness warning fires after a version change.

## Docs

- `README.md`: "Use the checks in another repo" explains packs.
- `sync` and `authoring-a-check.md`: prefer a pack over a copy.

## Acceptance criteria

- [ ] A work repo gets mstack's checks with one line in `.mstack.toml`, with no copied YAML.
- [ ] Upgrading mstack updates the checks in every repo that uses the pack.
- [ ] Overrides work without editing pack files.
