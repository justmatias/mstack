# mstack uses rulepack

- **Phase:** next
- **Depends on:** nothing open in this repo.
- **Runs in parallel with:** rulepack's [migrate-from-mstack](https://github.com/justmatias/rulepack/blob/main/docs/specs/migrate-from-mstack.md), which adds the enforcement code to rulepack while this spec deletes it here. Both PRs are open at the same time and merge back to back (rulepack first, `v0.1.0`), so no code is left dead or duplicated.

## Problem

mstack holds two things: content (prose rules, ast-grep checks, skills, agent settings) and all the code that enforces the checks (`lint`, `coverage`, `domain-check`, `exceptions`, `commit-msg`, `hook`, `init`, `packs`, `config`). The enforcement code is moving to [rulepack](https://github.com/justmatias/rulepack). If mstack keeps its copy, every fix lands twice or the two drift apart. And this repo would go on linting itself with code it no longer owns.

## Goal

mstack keeps only content and the tooling that installs it: `doctor`, `platform`, `cleanup`, `render-rule` and `skills-check`. Every other module goes. This repo lints itself with `rulepack`, the agent hooks it installs run `rulepack`, and `setup-mstack` installs `rulepack` next to `mstack`. The release is a major version.

## Out of scope

- **Shared packs.** `packs.toml` and the bundled packs are deleted, not replaced. rulepack's [pack-sources](https://github.com/justmatias/rulepack/blob/main/docs/specs/pack-sources.md) brings them back by loading packs from sources. Until then, this repo's checks run only here, and consumer repos that select packs stay on mstack `v6.x`.
- Any change to the content itself: rules, checks, rule tests, fixtures, skills.

## Design

**Delete.** Paths are under `src/mstack/` unless shown otherwise.

| What | Why |
| --- | --- |
| `lint.py`, `changed_files.py`, `project_paths.py`, `init.py`, `templates/`, `hooks.py` | moved to rulepack |
| `guards/check_exceptions.py`, `guards/check_commit_msg.py`, `guards/check_rule_coverage.py`, `guards/check_domain.py`, `guards/generic_names.txt` | moved to rulepack |
| `packs.py`, `packs.toml` (at the repo root), the wheel's `force-include` of content | packs return through rulepack's pack-sources |
| `config.py`, `.mstack.toml`, `mstack config` | nothing that stays reads them (see below) |
| `action.yml`, `.pre-commit-hooks.yaml` | each Action input and each hook runs a moved command; rulepack ships its own |
| tests for all of the above, and the slow `pre-commit try-repo` tests | moved with the code |

**What stays needs no config.** Of the modules that stay, only `cleanup` reads config, and only `rules_dir`, which in this checkout is always `rules/`. It uses `<checkout>/rules`. `StrictModel` is used only by `doctor`, so it moves into `doctor/model.py`. `render.py` and `guards/credit.py` stay for `render-rule`, `doctor` and `skills-check`. rulepack keeps its own copy of the frontmatter and credit helpers.

**What stays as content.** `rules/`, `lint/sgconfig.yml`, `lint/rules/`, `lint/rule-tests/` and `fixtures/` stay, along with `make demo` and the test that every file in `fixtures/invalid/` is still caught. Those test the checks, which are content. ast-grep reaches them through rulepack's dependencies.

**Integrate rulepack.**
- **Dev dependency.** `pyproject.toml` lists `rulepack` from git in the `dev` group. While both PRs are open, it is pinned to the head commit of rulepack's migration PR; the pin changes to `v0.1.0` before merging. `ast-grep-cli` and `import-linter` leave mstack's dependencies. mstack's code never imports rulepack.
- **Config.** `.rulepack.toml` replaces `.mstack.toml` with the same values: `rules_dir`, `sgconfig = "lint/sgconfig.yml"`, the `[scan]` exclude for `fixtures/invalid/**`, and `[domain_check]`.
- **Makefile.**
  - `lint-rules` and `lint-rules-changed` run `uv run rulepack lint`, with the same flags.
  - `repo-guards` runs `uv run mstack skills-check` and `uv run rulepack domain-check` on the agent config files.
  - `guards` and `demo` keep their behavior through rulepack.
- **Pre-commit.** The local `lint-rules` hook stays (`make lint-rules-changed STAGED=1`), and the commit-msg hook runs `uv run rulepack commit-msg`.
- **CI.**
  - The per-commit message check runs `uv run rulepack commit-msg`.
  - Portability runs `uv run rulepack lint`.
  - `action-self-test` and the slow tests go.
  - `versioning` stops moving a `v<major>` tag, since no Action is left to pin.
- **Agent settings.** `settings/claude.json`, `settings/codex.json` and `settings/cursor.json` run `rulepack hook post-edit` and `rulepack hook stop`.
- **Setup and doctor.**
  - `[tool.mstack] rulepack = "v0.1.0"` in `pyproject.toml` is the one place that names the rulepack version.
  - `setup-mstack` installs `rulepack` from git at that tag with `uv tool install`.
  - `doctor` checks that `rulepack` is on `PATH` and reports that version. This replaces the `find_tool` import from `lint`.
  - Installed settings that still run `mstack hook` show up as drift, which `setup-mstack` and `/repair` already fix.

**Command references.** Every mention of a moved command in skills, references, docs and the Makefile becomes `rulepack <command>`. That covers `lint`, `coverage`, `domain-check`, `exceptions`, `commit-msg`, `hook`, `init` and `config`. `doctor`, `platform`, `cleanup`, `render-rule` and `skills-check` keep the `mstack` prefix. Skill steps that use `mstack packs list` (`sync` and `references/authoring-a-check.md`) lose that step until pack-sources.

**Consumer repos.**
- A repo that does not select packs: rename `.mstack.toml` to `.rulepack.toml`, switch the pre-commit `repo:` and the Action to rulepack, and rerun `setup-mstack` for the agent hooks.
- A repo that selects packs: stay on mstack `v6.x` until rulepack's pack-sources ships.

`README.md` documents both cases.

**Cutover.** This is the same sequence as rulepack's spec:
1. Open both PRs.
2. Compare `mstack lint --json` at `main` with `rulepack lint --json` on this branch, and confirm they report the same findings.
3. Merge rulepack, which releases `v0.1.0`.
4. Change the pin here to `v0.1.0` and merge.

## Changes

- Delete everything in the "Delete" table.
- `src/mstack/cli.py`: five commands. `cleanup.py`: no config. `doctor/model.py`: `StrictModel`. `doctor/cli.py` and `doctor/tools.py`: the rulepack check.
- `pyproject.toml`: dependencies, `[tool.mstack] rulepack`, no `force-include`.
- `uv.lock`, `.rulepack.toml`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
- `settings/*.json`, `hooks/README.md`.
- Skills: `toolkit/sync` and its references, `toolkit/reflect`, `toolkit/repair`, `toolkit/integrate`, `toolkit/correct`, and any other skill that names a moved command. Also `.agents/skills/setup-mstack/SKILL.md`.
- `README.md`, `docs/workflow.md`, `docs/setup/`, `src/mstack/README.md`.

## Tests

- `uv run pytest` passes with the moved tests gone and no import of a deleted module.
- A guard test fails if any file under `skills/`, `settings/`, `docs/` or `.agents/`, or the `Makefile`, runs a moved command with the `mstack` prefix.
- `doctor` reports a missing `rulepack`.
- `cleanup` prunes rule backups beside `<checkout>/rules` with no config file present.
- `make lint-rules`, `make demo` and CI pass on this repo through rulepack.
- The parity check from "Cutover" step 2, recorded in the PR.

## Docs

- `README.md`: "What's inside" describes content plus the install tooling. Linting points at rulepack. Add the consumer migration section.
- `docs/workflow.md`: the daily loop with `rulepack lint`.
- `src/mstack/README.md`: the five remaining commands.
- `docs/specs/README.md`: remove this row in the PR that completes it.

## Acceptance criteria

- [ ] `mstack --help` lists only `cleanup`, `doctor`, `platform`, `render-rule` and `skills-check`.
- [ ] No mstack module imports ast-grep, import-linter or rulepack, and no `.mstack.toml` remains.
- [ ] This repo's CI is green on `rulepack` `v0.1.0`, with the same findings as before.
- [ ] A fresh `setup-mstack` run installs both CLIs, `mstack doctor` reports no errors, and agent hooks run `rulepack hook`.

## Open questions

- Whether `doctor` should fail when the installed `rulepack` is older than the pin, or only warn.
