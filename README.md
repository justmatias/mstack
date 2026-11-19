# mstack

My stack for guiding AI coding agents: one place for the agents, skills, rules, hooks and tools I use to steer them while they write code, plus the logbook of how and why each piece came to be.

Agents only follow what they are told and what is checked. Instructions scattered across projects drift, get copied by hand and are forgotten. `mstack` centralizes them so every project can pull the same set, and so each piece is tested and versioned like any other code.

## What lives here

| Piece | What it is |
| --- | --- |
| Rules | Team and personal conventions written in prose (`.cursor/rules/`), the single source of truth agents read before writing code. |
| Checks | The executable version of those rules (ast-grep, import-linter), run in the agent hook, in pre-commit and in CI. |
| Skills | Agent skills that keep prose rules and checks in sync and turn corrections into new rules. |
| Hooks | Agent hooks that run the checks while the agent edits, so mistakes surface before commit. |
| Tools | Small scripts and a setup CLI that install the pieces you want into a project or your user profile. |

The first feature is **rules as checks**: every rule that can be verified becomes an automated check, so conventions are enforced instead of re-flagged in code review. The reasoning behind it is in [`docs/design.md`](docs/design.md), and decisions taken during implementation are in [`docs/decisions.md`](docs/decisions.md).

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make setup        # uv sync, then asks which integrations to install
make lint         # every pre-commit hook on every file
make lint-rules   # the single command: tests, scan, contracts and guards
make demo         # scans demo/violations/ and expects it to fail
```

## What `make lint-rules` runs

1. `ast-grep test`: every check passes its valid and invalid cases.
2. `ast-grep scan`: the code follows every check (`demo/` excluded).
3. `lint-imports`: architecture contracts in `.importlinter`.
4. `scripts/check_rule_coverage.py`: every `.mdc` lists its checks, and every check points to an existing `.mdc` that lists it.
5. `scripts/check_exceptions.py`: every `ast-grep-ignore` has a `rule-exception` with reason, expiry and approval.
6. `scripts/check_no_domain_leak.py`: rules and checks contain no repo identifiers, URLs, emails or secrets.

`make lint-rules-changed` runs the same, but the scan only covers files changed relative to `origin/main`, and warnings count as errors there.

## Exceptions

```python
# rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
# ast-grep-ignore: prefer-pydantic-over-dataclass
```

## Setup options

`make setup` runs `scripts/setup.py`, which asks which integrations you want. Pass flags to skip the questions:

```bash
uv run python scripts/setup.py --yes                                  # everything, defaults
uv run python scripts/setup.py --with pre-commit --with claude-hook   # only these
uv run python scripts/setup.py --without cursor-hook --skills-scope global
uv run python scripts/setup.py --claude-settings project              # hook in the shared .claude/settings.json
uv run python scripts/setup.py --uninstall --yes                      # remove what install added
uv run python scripts/setup.py --dry-run --yes                        # show what would change
```

| Component | What it installs |
| --- | --- |
| `pre-commit` | `.git/hooks/pre-commit` (via `pre-commit install`), running the static checks and `make lint-rules-changed STAGED=1` |
| `claude-hook` | `PostToolUse` (`Edit\|Write`) in `.claude/settings.local.json` (default) or `.claude/settings.json` |
| `cursor-hook` | `postToolUse` (`Write`) in `.cursor/hooks.json`; findings come back as `additional_context` |
| `skills` | symlinks of `skills/*` into `.claude/skills/` and `.cursor/skills/` (or `~/` with `--skills-scope global`) |

Existing JSON files are merged, never overwritten, and backed up as `*.bak-<timestamp>`. Running setup twice changes nothing.

## Static checks and releases

`pre-commit` runs ruff, pylint, mypy, bandit, gitleaks, hookpin and generic file hygiene hooks, and also this repo's own `lint-rules` hook: `mstack` checks itself with the same rules it ships.

Versioning is automated with [python-semantic-release](https://python-semantic-release.readthedocs.io/). Commits and PR titles follow [Conventional Commits](https://www.conventionalcommits.org/); on every push to `main`, CI bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags the release and publishes it on GitHub (`feat` is a minor bump, `fix` and `perf` a patch).

## CI and branch protection

`.github/workflows/lint-rules.yml` has three jobs: `rules` (`make lint-rules-changed` on pull requests, `make lint-rules` on pushes to `main`), `demo-must-fail` (`make demo`) and `sync-drift` (`check_rule_coverage.py`).

To make `rules` block merges: **Settings → Branches → Add branch protection rule** (or **Rules → Rulesets**) for `main`, enable **Require status checks to pass before merging**, and add `rules`, `demo-must-fail`, `sync-drift` and the `ci.yml` static checks as required checks.
