# Pack sources

- **Phase:** next
- **Depends on:** nothing open. Builds on the bundled packs in `src/mstack/packs.py`, the pack selection and `[pack_overrides]` in `src/mstack/config.py`, and the pack scan in `src/mstack/lint.py`.

## Problem

A repo can only select packs that ship inside the installed mstack wheel. `pyproject.toml` force-includes `rules/`, `lint/rules/`, `lint/rule-tests/` and `packs.toml` as package data, and `packs.pack_root()` reads only that bundled copy or the checkout. Three consequences:

- Fixing one check means releasing the whole CLI.
- A team cannot publish its own pack. It has to copy checks into each repo, which is what packs were meant to replace.
- The linter engine cannot leave this repo ([rulepack-extraction](rulepack-extraction.md)) while it carries this repo's content inside its wheel.

## Goal

`mstack lint` loads packs from any git repo or local folder that has a `packs.toml`, pinned by a lockfile. mstack's own packs load the same way, and the wheel ships no content.

## Out of scope

- A registry or index of public packs. A source is a git URL or a path.
- Packs of prose rules. The linter only reads checks and their tests. Prose stays with mstack's setup and `coverage`.
- Rewriting check IDs. See "ID clashes" below.

## Design

**Source manifest.** Any repo or folder with a `packs.toml` at its root is a source. The manifest lists checks only:

```toml
# Optional. These are the defaults.
checks_dir = "lint/rules"
tests_dir = "lint/rule-tests"

[packs.python-core]
checks = ["no-bare-except", "no-swallowed-exception"]
```

The `rules = [...]` key goes away. The linter never reads prose, and pack prose is already verified in its source repo by that repo's own `coverage` run. A consumer repo's coverage only checks the consumer's own prose. Every path the manifest names must resolve inside the source root, or loading fails. The manifest is validated where it is read and trusted after that.

**Consumer config.** A repo declares its sources and selects packs as `<source>/<pack>`:

```toml
packs = ["mstack/python-core", "mstack/testing", "team/backend"]

[sources.mstack]
git = "https://github.com/justmatias/mstack"
ref = "v7.0.0"          # tag, branch or SHA; the lockfile pins the commit

[sources.team]
path = "../team-rules"  # relative to the config file
```

A source has exactly one of `git` or `path`. A bare pack name such as `python-core` is an error, and the message suggests `mstack/python-core` with the `[sources.mstack]` block to add. There is no implicit default source and no compatibility alias. The few consumer repos migrate in the same release.

**Lockfile.** `mstack packs lock` resolves each git source's `ref` to a commit and writes `.mstack.lock` next to the config:

```toml
[sources.mstack]
git = "https://github.com/justmatias/mstack"
ref = "v7.0.0"
commit = "<40-hex sha>"
```

- `mstack lint` never writes the lock and never moves a pin. It fails when a git source is missing from the lock, or when its `git` or `ref` differs from the config, and the message says to run `mstack packs lock`. CI is reproducible because the commit is checked in.
- `mstack packs update [<source>...]` re-resolves refs and rewrites the lock.
- Path sources are not locked: they are local by definition. `mstack lint --changed` in CI warns when a selected pack comes from a path source outside the repo.

**Cache.** Fetched sources live in `$XDG_CACHE_HOME/mstack/sources/<sha256 of url>/<commit>/` (default `~/.cache/...`), extracted with `git archive` from a `--filter=blob:none` clone of the URL. Each commit is written to a temporary folder and renamed into place, so an interrupted fetch never leaves a half-written commit, and a rerun only fetches what is missing. git's own credentials handle private sources; mstack stores none.

**Agent hooks never fetch.** `mstack hook` runs with a time budget. If a locked commit is not in the cache, the hook skips pack checks for that run and logs one line that tells the user to run `mstack packs lock`. That command fetches as well as locks. `mstack lint` fetches as needed.

**Host defaults.** `~/.config/mstack/config.toml` may declare `[sources]` next to `packs`. Its lock is `~/.config/mstack/config.lock`, written by `mstack packs lock --host`. The existing rule still holds: a repo's `packs` list replaces the host list, and CI selects packs in the repo.

**ID clashes.** ast-grep rule IDs must be unique, and existing `ast-grep-ignore: <id>` comments and `[pack_overrides]` refer to bare IDs, so IDs are never rewritten.
- A repo's own check still wins over a pack check with the same ID, and the clash is logged. This is current behavior.
- Two selected packs that define the same ID is an error naming both sources. The user removes one pack or disables one check. Disabling the ID covers both sources, which is the same thing as removing one of them.

**mstack becomes a source.** This repo's `packs.toml` drops `rules = [...]`. The wheel stops force-including `packs.toml`, `rules/`, `lint/rules/` and `lint/rule-tests/`, and `pack_root()` goes away. In this checkout, tests use `[sources.mstack] path = "."`.

**`mstack packs list`** lists the packs of every declared source, with each source's locked commit. `--json` gives the same data for scripts.

## Changes

- `src/mstack/packs.py`: manifest model with path containment, source models (`GitSource`, `PathSource`), resolution, cache, lock read and write, `lock`/`update`/`list` subcommands. `pack_root()` is deleted.
- `src/mstack/config.py`: `sources` on `ProjectConfig` and `HostConfig`; `<source>/<pack>` validation.
- `src/mstack/lint.py`: load packs through the lock; ID-clash error between packs.
- `src/mstack/hooks.py`: skip uncached pack checks instead of fetching.
- `src/mstack/guards/check_rule_coverage.py`: drop pack prose (`pack_coverage`).
- `packs.toml`: remove `rules` lists.
- `pyproject.toml`: remove the `force-include` and sdist entries for content.
- `src/mstack/templates/mstack.toml`: `mstack init` writes the `[sources.mstack]` block, pinned to the running release's tag.
- `tests/test_packs.py`: replace the "every rule belongs to a pack" test with "every check in `lint/rules/` belongs to exactly one pack".

## Tests

Every git test uses a local bare repo made in `tmp_path` as the source URL, so no test reaches the network.

- A consumer with a git source and a lock fails `mstack lint` on a violating file, and passes after disabling the check.
- A path source works without a lock.
- Missing lock, and a lock whose `ref` differs from the config, each fail `lint` with the "run `mstack packs lock`" message. `lint` leaves the lock file untouched.
- `packs lock` twice gives the same file. `packs update` after a new commit on the source's branch moves the pin.
- A manifest path that escapes the source root (`../`) is rejected.
- Two packs defining the same ID fail with both source names. A local check with a pack's ID wins and logs.
- A bare pack name fails with the suggested fix.
- The post-edit hook with an uncached commit runs local checks, skips pack checks, and makes no clone.
- The wheel built by `uv build` contains no `.yml` or `.mdc` content.

## Docs

- `README.md`, "Use the checks in another repo": sources, lock, `packs lock` and `packs update`, pinning, and the migration from bare pack names.
- `docs/workflow.md`: the lock in the consumer setup steps.
- `skills/toolkit/sync/SKILL.md` and `references/authoring-a-check.md`: propose `<source>/<pack>`, and a team source when a check is shared across repos.

## Acceptance criteria

- [ ] A repo uses checks from mstack and from a second git repo, pinned by a checked-in lock, and CI runs them with no mstack checkout.
- [ ] Fixing a check in a source and running `mstack packs update` in a consumer picks up the fix without a new mstack release.
- [ ] The mstack wheel ships no rules, checks or rule tests.
- [ ] Agent hooks never touch the network.

## Open questions

- Whether `ref` should reject branch names, to discourage moving refs. The lock pins either way.
