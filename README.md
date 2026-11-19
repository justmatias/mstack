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
make demo         # scans fixtures/invalid/ and expects it to fail
make test         # pytest: checks, guards, setup CLI, skills and personal rules
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
| `claude-hook` | `PostToolUse` (`Edit\|Write\|MultiEdit`) in `.claude/settings.local.json` (default) or `.claude/settings.json` |
| `cursor-hook` | `postToolUse` (no matcher: every tool, acting only on `.py` file paths) in `.cursor/hooks.json`; findings come back as `additional_context`. `.cursor/hooks.json` is gitignored here; to share it with the team, `git add -f` it (Cursor has no local-only hooks file) |
| `skills` | symlinks of `skills/*` into `.claude/skills/` and `.cursor/skills/` (or `~/` with `--skills-scope global`) |

Existing JSON files are merged, never overwritten, and backed up as `*.bak-<timestamp>`. Running setup twice changes nothing; re-running it upgrades the matchers of hooks installed by an older version.

To see which tools a real Cursor (or Claude Code) session sends to the hooks, set `MSTACK_HOOK_DEBUG=1` in the agent's environment: every call appends its tool name and input keys to `$MSTACK_HOOK_DEBUG_LOG` (default `mstack-hooks.log` in the temp folder).

## Static checks and releases

`pre-commit` runs ruff, pylint, mypy, bandit, gitleaks, hookpin and generic file hygiene hooks, and also this repo's own `lint-rules` hook: `mstack` checks itself with the same rules it ships.

Versioning is automated with [python-semantic-release](https://python-semantic-release.readthedocs.io/). Commits and PR titles follow [Conventional Commits](https://www.conventionalcommits.org/); on every push to `main`, CI bumps the version in `pyproject.toml`, updates `CHANGELOG.md`, tags the release and publishes it on GitHub (`feat` is a minor bump, `fix` and `perf` a patch).

## CI and branch protection

The `static-checks` job in `.github/workflows/ci.yml` runs every pre-commit hook (`make lint`), then `make lint-rules` on the whole repo, `make lint-rules-changed` on the files a pull request changes (warnings fail there), `make demo` and `make test`.

To make it block merges: **Settings → Branches → Add branch protection rule** (or **Rules → Rulesets**) for `main`, enable **Require status checks to pass before merging**, and add both `Static checks` jobs (one per Python version) as required checks.

## Personal rules (every repo, shared with no one)

Your own checks live in `$MY_RULES_HOME` (default `~/.config/my-rules/`), apply in every repo you work in, and write nothing into those repos. They warn in the agent and at commit time; CI is left out on purpose, because it belongs to each team.

```bash
uv run python scripts/setup.py user              # asks which parts to install
uv run python scripts/setup.py user --yes --replace-hooks-path
uv run python scripts/setup.py user --uninstall --yes
```

| Component | What it does |
| --- | --- |
| `rules` | Copies `user-level/` to `$MY_RULES_HOME` **only if it does not exist**, links every git hook name in `githooks/` to `bin/git-hook-chain`, and copies the example prose rules to `~/.cursor/rules/my-*.mdc` |
| `claude-hook` | Merges a `PostToolUse` (`Edit\|Write\|MultiEdit`) hook running `bin/claude-post-edit` into `~/.claude/settings.json` |
| `cursor-hook` | Merges a `postToolUse` hook (no matcher) running `bin/cursor-after-edit` into `~/.cursor/hooks.json` |
| `git-hooks` | `git config --global core.hooksPath $MY_RULES_HOME/githooks` |
| `skills` | Links the three skills into `~/.claude/skills/` and `~/.cursor/skills/` |

- `bin/my-rules-check [--with-repo] <files>` is the single command: it filters by the rules' languages, drops anything in `ignore-paths.txt` (`<glob> [rule-id]`), and runs only over the given files, so old mistakes you did not write never show up. `--with-repo` also runs the current repo's `lint-rules/`.
- The agent hooks run the repo set too, unless the repo already has its own project hook (then only the personal set runs, so nothing runs twice).
- `MY_RULES_DISABLE=1` turns everything off for one command.
- Uninstall restores the previous `core.hooksPath`, removes the hook entries (restoring the original bytes of each JSON file), and deletes only the personal-set files you never modified.
- Optional: `git init` in `$MY_RULES_HOME` to version your set privately. `ignore-paths.txt` is already in its `.gitignore`, because it holds work repo paths.

### Pitfalls of the global git hook

- **`pre-commit install` refuses to run** when a global `core.hooksPath` is set. That is why `git-hook-chain` calls `pre-commit hook-impl` directly, for the hook types the repo would have installed (`default_install_hook_types`, default `pre-commit`). `hook-impl` is internal to pre-commit: the chain is tested with pre-commit 4 (`make test` fails if the flags it uses disappear).
- **Repos using husky** set `core.hooksPath` at repo level, which takes precedence over the global one. There the personal git hook does not run; only the agent hooks remain.
- **An existing global `core.hooksPath`** is never replaced silently: the installer warns and skips unless you pass `--replace-hooks-path`, and the previous value is restored on uninstall.
- A repo's own `.git/hooks/<name>` still runs through the chain (with the same arguments and stdin), unless pre-commit generated it, in which case pre-commit is called instead.
