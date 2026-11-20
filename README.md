# mstack

My stack for guiding AI coding agents: one place for the skills, rules, checks and tools I use to steer them while they write code.

Agents only follow what they are told and what is checked. Instructions scattered across projects drift, get copied by hand and are forgotten. `mstack` centralizes them so every project can pull the same set, and so each piece is tested and versioned like any other code.

## What lives here

| Piece | Where | What it is |
| --- | --- | --- |
| Rules | `rules/` | Conventions written in prose (`.mdc`), the single source of truth agents read before writing code. |
| Checks | `lint/` | The executable version of those rules (ast-grep, plus import-linter in `.importlinter`), run in pre-commit and in CI. |
| Skills | `skills/` | Agent skills that keep prose rules and checks in sync, turn corrections into new rules, integrate skills from GitHub with their credit (`integrate-skills`), and install mstack itself (`setup-mstack`). |
| Tools | `src/mstack/`, `scripts/` | The `mstack` CLI (guards) and the repo tooling behind the `make` targets. |

The first feature is **rules as checks**: every rule that can be verified becomes an automated check, so conventions are enforced instead of re-flagged in code review.

## Rules

| Rule | What it covers |
| --- | --- |
| `architecture-layers.mdc` | Dependency direction between the domain, infra and api layers. |
| `error-handling.mdc` | No bare `except`, no swallowed exceptions. |
| `logging.mdc` | Logging instead of `print` in application code. |
| `naming.mdc` | Naming and function size (judgment only, reviewed by an LLM on the PR). |
| `python-models.mdc` | How to define data models in Python. |

Each rule ends with a `## Checks` section naming the checks in `lint/` (or `.importlinter`) that enforce it, and each check points back to its rule through `metadata.source`. `mstack coverage` fails when the two sides disagree, so the rule files themselves are the index: there is no separate table to regenerate.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make setup        # uv sync (dev dependencies)
make lint         # every pre-commit hook on every file
make lint-rules   # the single command: tests, scan, contracts and guards
make demo         # scans fixtures/invalid/ and expects it to fail
make test         # pytest: checks, guards and skills
```

The skills call the guards as `mstack <command>` from whatever repo they run in. Install the CLI once, on your `PATH`:

```bash
uv tool install --editable .   # from this checkout; `mstack --help` lists the commands
```

## What `make lint-rules` runs

1. `ast-grep test`: every check passes its valid and invalid cases.
2. `ast-grep scan`: the code follows every check (`fixtures/invalid/` excluded).
3. `lint-imports`: architecture contracts in `.importlinter`.
4. `mstack coverage`: every `.mdc` lists its checks, and every check points to an existing `.mdc` that lists it.
5. `mstack exceptions`: every `ast-grep-ignore` has a `rule-exception` with reason, expiry and approval.
6. `mstack leak-check`: rules and checks contain no repo identifiers, URLs, emails or secrets.

`make lint-rules-changed` runs the same, but the scan only covers files changed relative to `origin/main` (`BASE_REF` overrides it and must exist), and warnings count as errors there. CI runs it on every pull request against the PR's base branch, so a `warning` rule fails on new or touched code even when pre-commit was skipped.

## Exceptions

```python
# rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
# ast-grep-ignore: no-manual-init-boilerplate
```

## Installing the skills and rules

Open this repo in Claude Code or Cursor and ask the agent to "set up mstack following skills/setup-mstack/SKILL.md". There is no install script: the skill is a set of instructions the agent follows, asking you before every change.

1. It asks whether you use Claude Code, Cursor, or both.
2. It compares every skill in `skills/` (except `setup-mstack` itself) and every rule in `rules/` with what you already have, including similar skills such as pstack `reflect`.
3. For each one it proposes add, update, replace, discard or combine, shows the diffs, and waits for your answer.

| You use | Skills go to | Rules go to |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `~/.claude/rules/<name>.md` |
| Cursor | `~/.cursor/skills/` | Cursor Settings → Rules (Cursor does not load rule files from `~/.cursor/rules/`; the skill prints them for you to paste) |
| Both | `~/.claude/skills/` only, because Cursor loads that folder too | both of the above |

- Copies, not symlinks: `skills/` and `rules/` in this repo stay the source of truth. To update, pull this repo and run the skill again.
- Anything replaced or removed is backed up to `<folder>/.mstack-backups/<timestamp>/`, never next to the skills or rules.
- The installed skills run the guards as `mstack <command>`, so the skill also installs the `mstack` CLI from this checkout (`uv tool install --editable .`).

## Static checks and releases

`pre-commit` runs ruff, pylint, mypy, bandit, gitleaks, hookpin and generic file hygiene hooks, and also this repo's own `lint-rules` hook: `mstack` checks itself with the same rules it ships.

Versioning is automated with [python-semantic-release](https://python-semantic-release.readthedocs.io/). Commits and PR titles follow [Conventional Commits](https://www.conventionalcommits.org/); on every push to `main`, CI bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags the release and publishes it on GitHub (`feat` is a minor bump, `fix` and `perf` a patch).

## CI and branch protection

The `static-checks` job in `.github/workflows/ci.yml` runs every pre-commit hook (`make lint`), then `make lint-rules` on the whole repo, `make lint-rules-changed` on the files a pull request changes (warnings fail there), `make demo` and `make test`.

To make it block merges: **Settings → Branches → Add branch protection rule** (or **Rules → Rulesets**) for `main`, enable **Require status checks to pass before merging**, and add both `Static checks` jobs (one per Python version) as required checks.
