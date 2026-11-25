# mstack uses rulepack

- **Phase:** next
- **Depends on:** [rulepack-extraction](rulepack-extraction.md). Needs a public rulepack release with `lint --json --files` and `checks --json`.

## Problem

Once rulepack is released, mstack still has its own copy of the linter (`lint.py`, `packs.py`, `hooks.py`, `init.py`, and others). Two copies drift. Skills, settings, CI and docs would keep running `mstack lint` while fixes land in rulepack.

## Goal

mstack keeps a small CLI for the stack itself: `doctor`, `platform`, `cleanup`, `render-rule`, `skills-check`, `coverage` and `domain-check`. It deletes everything that moved, and every skill, setting, workflow and doc runs `rulepack` for linting. The release that does this is a major version.

## Out of scope

- New rulepack features.
- An automatic migration command for consumer repos (open question).

## Design

**Delete what moved.** These go: `lint.py`, `changed_files.py`, `packs.py`, `init.py`, `hooks.py`, `templates/`, `guards/check_exceptions.py`, `guards/check_commit_msg.py`, `action.yml`, and their tests. Their entries go from `cli.py`'s `COMMANDS`. `ast-grep-cli` and `import-linter` leave mstack's runtime dependencies. rulepack is a dev dependency only, pinned to a minor range for this repo's own CI. mstack's code calls the `rulepack` binary and never imports it, so the two release on their own schedules.

**What stays, and how it talks to the linter.**
- `coverage` resolves `enforced-by:` through `rulepack checks --json`. It no longer reads an sgconfig or packs.
- `doctor` checks that `rulepack` is on `PATH`, and that its version is in the range `setup-mstack` installs. This replaces the `find_tool("ast-grep")` import from `lint`.
- `domain-check`, `skills-check`, `render-rule`, `platform` and `cleanup` are unchanged.

**Config split.** `.mstack.toml` keeps only `rules_dir` and `[domain_check]`. Every other key moves to `.rulepack.toml` (formats in [pack-sources](pack-sources.md)), and the lock becomes `rulepack.lock`. mstack fails on a leftover lint key in `.mstack.toml` with a message naming its new home. This repo's own `.mstack.toml` is split the same way.

**This repo as a source.** `packs.toml`, `lint/rules/` and `lint/rule-tests/` stay where they are. Releases of mstack are now also releases of its packs: consumers pin `[sources.mstack] ref` to an mstack tag.

**Agent hooks.** `settings/claude.json`, `settings/codex.json` and `settings/cursor.json` run `rulepack hook post-edit` and `rulepack hook stop`. `doctor` already reports a drifted installed settings file, and `setup-mstack` updates it.

**Setup.** `setup-mstack` installs both CLIs:
- `uv tool install --editable <mstack> --reinstall`
- `uv tool install git+https://github.com/justmatias/rulepack@<pinned tag>`

The pinned tag lives in one place that both `setup-mstack` and `doctor` read: a `[tool.mstack] rulepack = "vX.Y.Z"` entry in `pyproject.toml`.

**Pre-commit hooks this repo ships.** `.pre-commit-hooks.yaml` keeps `mstack-domain-check`, and `mstack-rules`, which now runs `mstack coverage` only. The lint, exceptions and imports hooks are deleted. Consumers use rulepack's hooks.

**Command references.** Rewrite each command that moved, in skills, references, docs and the Makefile:

| Before | After |
| --- | --- |
| `mstack lint`, `mstack packs`, `mstack init`, `mstack exceptions`, `mstack commit-msg`, `mstack hook` | `rulepack <same>` |
| `mstack lint --only coverage` / `domain-check` | `mstack coverage` / `mstack domain-check` |

`doctor`, `coverage`, `domain-check`, `render-rule`, `platform`, `skills-check` and `cleanup` keep the `mstack` prefix.

**Makefile.**
- `lint-rules` runs `rulepack lint`, then `mstack coverage`, `mstack domain-check` and `repo-guards`.
- `lint-rules-changed` passes `--changed` to rulepack.
- `demo` runs ast-grep through rulepack's environment.

**Consumer migration**, documented in `README.md`:
1. Install rulepack.
2. Move the lint keys from `.mstack.toml` to `.rulepack.toml`, and rename `.mstack.lock` to `rulepack.lock`.
3. Replace the pre-commit `repo:` and the Action with rulepack's.
4. Rerun `setup-mstack` to update agent hooks.

## Changes

- Delete: the modules, tests and `action.yml` listed above.
- `src/mstack/cli.py`, `config.py` (only mstack's keys), `doctor/cli.py`, `doctor/tools.py`, `guards/check_rule_coverage.py`.
- `pyproject.toml`: dependencies, the `[tool.mstack] rulepack` pin, version major bump.
- `.mstack.toml` split into `.mstack.toml` and `.rulepack.toml`, plus `rulepack.lock`. `Makefile`, `.pre-commit-hooks.yaml`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, including the per-commit `commit-msg` job.
- `settings/*.json`, `hooks/README.md`.
- Skills: `toolkit/sync` and its references, `toolkit/reflect`, `toolkit/repair`, `toolkit/integrate`, `toolkit/correct`, and any other skill that names a moved command. `.agents/skills/setup-mstack/SKILL.md`.
- `README.md`, `docs/workflow.md`, `docs/setup/`, `src/mstack/README.md`, `AGENTS.md`.

## Tests

- `uv run pytest` passes with the moved tests gone and nothing importing a deleted module.
- A guard test: no file under `skills/`, `settings/`, `docs/`, `.agents/` or the `Makefile` runs a moved command with the `mstack` prefix.
- `coverage` with a stubbed `rulepack checks --json` output resolves `enforced-by:` to local and pack checks, and reports a missing one.
- `doctor` reports a missing `rulepack` and a version outside the pin.
- A leftover lint key in `.mstack.toml` fails with the migration message.
- `make lint-rules` and CI pass on this repo using rulepack.

## Docs

- `README.md`: "What's inside" and "Getting started" name both CLIs, and a migration section for consumer repos.
- `docs/workflow.md`: the daily loop with `rulepack lint`.
- `src/mstack/README.md`: only the remaining commands.
- `AGENTS.md`: "run `make lint-rules-changed`" stays, since the Makefile hides the tool.

## Acceptance criteria

- [ ] `mstack --help` lists only `cleanup`, `config`, `coverage`, `doctor`, `domain-check`, `platform`, `render-rule` and `skills-check`.
- [ ] No mstack module imports ast-grep, import-linter or rulepack.
- [ ] A fresh `setup-mstack` run installs both CLIs, and `mstack doctor` reports no errors.
- [ ] Agent hooks on a fresh machine run `rulepack hook`.
- [ ] A consumer repo migrated with the README steps passes `rulepack lint` in CI.

## Open questions

- Whether rulepack should offer `rulepack init --from-mstack` to move the keys out of `.mstack.toml`, or whether the README steps are enough for the few consumer repos.
- Whether `mstack config` is still worth keeping for two keys, or should be folded into `doctor` output.
