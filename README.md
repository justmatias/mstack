# mstack

My stack for guiding AI coding agents: one place for the skills, rules, checks and tools I use to steer them while they write code, plus the logbook of how and why each piece came to be.

Agents only follow what they are told and what is checked. Instructions scattered across projects drift, get copied by hand and are forgotten. `mstack` centralizes them so every project can pull the same set, and so each piece is tested and versioned like any other code.

## What lives here

| Piece | Where | What it is |
| --- | --- | --- |
| Rules | `rules/` | Conventions written in prose (`.mdc`), the single source of truth agents read before writing code. |
| Checks | `lint/` | The executable version of those rules (ast-grep, plus import-linter in `.importlinter`), run in pre-commit and in CI. |
| Skills | `skills/` | Agent skills that keep prose rules and checks in sync, turn corrections into new rules, and install mstack itself (`setup-mstack`). |
| Tools | `scripts/` | Guards and generators behind the `make` targets. |

The first feature is **rules as checks**: every rule that can be verified becomes an automated check, so conventions are enforced instead of re-flagged in code review. The reasoning behind it is in [`docs/design.md`](docs/design.md), and decisions taken during implementation are in [`docs/decisions.md`](docs/decisions.md).

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make setup        # uv sync (dev dependencies)
make lint         # every pre-commit hook on every file
make lint-rules   # the single command: tests, scan, contracts and guards
make demo         # scans fixtures/invalid/ and expects it to fail
make test         # pytest: checks, guards and skills
```

## What `make lint-rules` runs

1. `ast-grep test`: every check passes its valid and invalid cases.
2. `ast-grep scan`: the code follows every check (`fixtures/invalid/` excluded).
3. `lint-imports`: architecture contracts in `.importlinter`.
4. `scripts/guards/check_rule_coverage.py`: every `.mdc` lists its checks, and every check points to an existing `.mdc` that lists it.
5. `scripts/guards/check_exceptions.py`: every `ast-grep-ignore` has a `rule-exception` with reason, expiry and approval.
6. `scripts/guards/check_no_domain_leak.py`: rules and checks contain no repo identifiers, URLs, emails or secrets.

`make lint-rules-changed` runs the same, but the scan only covers files changed relative to `origin/main`, and warnings count as errors there.

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
- `~/.config/mstack/config.json` records where this repo is. The installed skills read it (or `$MSTACK_HOME`, which takes priority) to find `scripts/`.

## Static checks and releases

`pre-commit` runs ruff, pylint, mypy, bandit, gitleaks, hookpin and generic file hygiene hooks, and also this repo's own `lint-rules` hook: `mstack` checks itself with the same rules it ships.

Versioning is automated with [python-semantic-release](https://python-semantic-release.readthedocs.io/). Commits and PR titles follow [Conventional Commits](https://www.conventionalcommits.org/); on every push to `main`, CI bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags the release and publishes it on GitHub (`feat` is a minor bump, `fix` and `perf` a patch).

## CI and branch protection

The `static-checks` job in `.github/workflows/ci.yml` runs every pre-commit hook (`make lint`), then `make lint-rules` on the whole repo, `make demo` and `make test`.

To make it block merges: **Settings → Branches → Add branch protection rule** (or **Rules → Rulesets**) for `main`, enable **Require status checks to pass before merging**, and add both `Static checks` jobs (one per Python version) as required checks.
