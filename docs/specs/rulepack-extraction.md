# Extract the linter into rulepack

- **Phase:** next
- **Depends on:** [pack-sources](pack-sources.md), because the wheel must ship no content before the engine can leave this repo. Also rulepack's [bootstrap](https://github.com/justmatias/rulepack/blob/main/docs/specs/bootstrap.md), so the repo already has its packaging, CI, pre-commit and releases, and this spec only adds code.

## Problem

`src/mstack/` holds two tools with different users and different release needs:

- **A linter:** `lint`, `packs`, `init`, `exceptions`, `commit-msg`, `hook`, plus `changed_files.py` and most of `config.py`. It runs ast-grep and import-linter checks in any repo, and knows nothing about skills or agent install folders.
- **The stack's own tooling:** `doctor`, `platform`, `cleanup`, `render-rule`, `skills-check`, `coverage`, `domain-check`. These install and verify the skills and prose rules in this repo.

Because they share one package, a linter feature waits on the stack's release, and the linter cannot become a tool of its own. Pack sources make the linter's content external, so the engine itself can move.

## Goal

[`justmatias/rulepack`](https://github.com/justmatias/rulepack) is a standalone Python CLI, `rulepack`, with the linter's history, tests and CI, and a first release (`v0.1.0`) that runs this repo's packs as a git source. This spec covers only the rulepack side. mstack keeps working unchanged until [mstack-uses-rulepack](mstack-uses-rulepack.md).

## Out of scope

- Removing anything from mstack (next spec).
- New linter features beyond the two interfaces mstack needs (below). Later features are specced in rulepack's own `docs/specs/`.
- Publishing to PyPI (open question).

## Design

**What moves.**

| From mstack | To rulepack |
| --- | --- |
| `lint.py`, `changed_files.py`, `packs.py`, `init.py`, `project_paths.py`, `templates/` | same names under `src/rulepack/` |
| `hooks.py` | `rulepack hook post-edit`/`stop` |
| `guards/check_exceptions.py`, `guards/check_commit_msg.py` | `rulepack exceptions`, `rulepack commit-msg` |
| the lint keys of `config.py` (`packs`, `sources`, `pack_overrides`, `sgconfig`, `importlinter`, `pre_commit_config`, `scan`, `changed`, `commits`, `hooks`) | `rulepack/config.py` |
| `action.yml`, the lint, rules-test, exceptions and imports entries of `.pre-commit-hooks.yaml` | rulepack's root |
| the matching tests under `tests/` | rulepack's `tests/` |

**Why the borderline commands go to rulepack.**
- **Hooks:** they need the linter's config, its file selection and its hook settings. Parsing an agent's hook payload is a small, stable part of linting while an agent edits. In mstack it would import the linter's internals or duplicate them.
- **`commit-msg`:** it enforces a rule as a check, which is the linter's job, and its `[commits]` settings already live in the lint config.

**What stays in mstack:** `coverage`, which reads prose; `domain-check`, which guards repos that author rules and prose; and everything that installs skills.

**Config and lock.** The consumer config is `.rulepack.toml` and the lock is `rulepack.lock`. Their formats are the ones from [pack-sources](pack-sources.md), minus the mstack-only keys (`rules_dir`, `domain_check`). The host config is `$XDG_CONFIG_HOME/rulepack/config.toml` and the cache is `$XDG_CACHE_HOME/rulepack/`. The source manifest keeps its name, `packs.toml`, so mstack and any other source need no change.

**Lint steps.** `rulepack lint` runs `test`, `scan`, `imports` and `exceptions`. The `coverage` and `domain-check` steps leave the linter, so `--only`/`--skip` no longer accept them.

**Interfaces mstack relies on.** These are the only new code in this spec, and they are versioned as public API from `v0.1.0`:
- `rulepack lint --json --files <paths...>`: rulepack applies its own `[scan]` filters to the given paths. Callers pass what they have and do not filter first.
- `rulepack checks --json`: every resolved check (local and pack), with ID, severity, source, pack and file. mstack's `coverage` uses it to resolve `enforced-by:` without reading the linter's config.

**History.** Run `git filter-repo` over a clone of mstack, keeping only the moved paths, so `git log` and blame follow each file. Merge that history into rulepack's `main` with `--allow-unrelated-histories`. The package and import renames (`mstack` → `rulepack`) are one commit on top. All of it lands in one PR titled `feat: move the linter from mstack`. That PR's title releases `v0.1.0`, because the bootstrap sets `major_on_zero = false`.

**Distribution.** The same as mstack today: `uv tool install git+https://github.com/justmatias/rulepack@<tag>`, `uvx --from git+...@<tag> rulepack lint`, a pre-commit hook at `rev: <tag>`, and the GitHub Action at `justmatias/rulepack@v0`. The bootstrap makes the repo public. The `versioning` job moves the `v0` tag with each release.

**Dogfooding.** The bootstrap lints rulepack with mstack's published hooks at a pinned tag. This spec replaces them: rulepack lints itself with its own code, using `.rulepack.toml` to select `mstack/python-core` and `mstack/testing` at a pinned mstack tag, and the per-commit `commit-msg` CI step calls `uv run rulepack commit-msg`. The dependency runs one way: rulepack's code never imports or names mstack, only its config does.

## Changes

All in rulepack, on top of the bootstrapped toolchain:

- `src/rulepack/` and `tests/`, which replace the bootstrap's minimal CLI. Its `--version` test stays.
- `pyproject.toml`: the runtime dependencies `ast-grep-cli`, `import-linter`, `pydantic` and `pyyaml`, plus the `slow` pytest marker. Also `uv.lock`, and the pylint and mypy `additional_dependencies` in `.pre-commit-config.yaml`.
- `action.yml`, `.pre-commit-hooks.yaml`, and new CI jobs: `action-self-test`, the slow `pre-commit try-repo` tests, and `rulepack lint` in the portability matrix.
- `.pre-commit-config.yaml`: mstack's hooks are replaced by local `rulepack lint` and `rulepack commit-msg` hooks. `.mstack.toml` is replaced by `.rulepack.toml`, plus `rulepack.lock`.
- `README.md`: the status line becomes usage docs covering config, sources, the lock, CI, pre-commit and agent hooks.

## Tests

- The moved test suite passes under the new package name, with no test reaching the network (local bare repos as sources).
- `rulepack lint` in a temporary consumer with `[sources.mstack]` pinned to a local bare clone of this repo fails on a violating file.
- `rulepack lint --json --files` filters paths by `[scan]` excludes and extensions.
- `rulepack checks --json` lists local and pack checks, marks local overrides, and matches a JSON schema checked into rulepack's tests.
- `rulepack hook post-edit` with a sample Claude Code and Codex payload lints the edited file.
- A clean CI job installs the tagged release with `uvx` and runs it on a fixture repo.

## Docs

- rulepack's `README.md` (above).
- In mstack, nothing changes until the next spec. `README.md` may mention that rulepack is in progress.

## Acceptance criteria

- [ ] `justmatias/rulepack` has the moved files' history, and its CI is green while rulepack lints itself with mstack's packs.
- [ ] `v0.1.0` is tagged. `uvx --from git+https://github.com/justmatias/rulepack@v0.1.0 rulepack lint` runs mstack's packs in a consumer repo.
- [ ] `rulepack lint --json --files` and `rulepack checks --json` are documented as stable.
- [ ] No file in rulepack names mstack outside config and docs.

## Open questions

- PyPI: `rulepack` is free there today. Publishing makes `uvx rulepack` work without a git URL. It can come with `v0.1.0` or later.
- Whether `init` keeps scaffolding a prose rules folder (`--rules-dir`). The linter never reads prose, so that may belong to mstack's `sync`.
