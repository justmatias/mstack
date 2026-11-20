# mstack

My stack for guiding AI coding agents: the skills, rules and checks I use to steer them while they write code, kept in one place, tested and versioned like any other code.

Agents follow what they are told and what is checked. So every rule that can be verified becomes an automated check (**rules as checks**), and conventions are enforced instead of re-flagged in code review.

## What's inside

| Folder | What it is |
| --- | --- |
| `rules/` | Conventions in prose (`.mdc`), the source of truth agents read before writing code. |
| `lint/` | The checks that enforce those rules (ast-grep), plus architecture contracts in `.importlinter`. |
| `skills/` | Agent skills that keep rules and checks in sync and turn corrections into new rules. |
| `src/mstack/` | The `mstack` CLI: the guards the skills and `make` targets run. |

## Getting started

You need [`uv`](https://docs.astral.sh/uv/), git, and Claude Code or Cursor.

**1. Clone and install the CLI.** The skills run the guards as `mstack <command>`, so it has to be on your `PATH`.

```bash
git clone https://github.com/justmatias/mstack
cd mstack
make setup                      # dev dependencies
uv tool install --editable .    # the mstack CLI; `mstack --help` lists the commands
```

**2. Install the skills and rules.** Open this repo in Claude Code or Cursor and ask the agent to *"set up mstack following skills/setup-mstack/SKILL.md"*. It asks which tool you use, compares each skill and rule with what you already have, and waits for your answer before every change.

| You use | Skills go to | Rules go to |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `~/.claude/rules/` |
| Cursor | `~/.cursor/skills/` | Cursor Settings → Rules (the skill prints them for you to paste) |
| Both | `~/.claude/skills/` (Cursor loads it too) | both of the above |

They are copies, not symlinks, and anything replaced is backed up to `<folder>/.mstack-backups/<timestamp>/`.

**3. Use the skills in your projects.**

| Skill | Use it to |
| --- | --- |
| `sync-rules` | Adopt rules as checks in a repo: turn its prose rules (`.cursor/rules`, `AGENTS.md`, `CLAUDE.md`) into checks, and keep both in sync. |
| `reflect-rules` | Turn the corrections and preferences from the current session into rules and checks. |
| `correct-rules` | Find the mistakes that keep repeating in a repo and make each one impossible. |
| `integrate-skills` | Bring a skill from a GitHub URL into `skills/`, with its license and credit. |

**4. Update.** Pull this repo and run step 2 again. mstack records what it installed, so upstream changes update on their own (with a backup), your own edits are kept, and it only asks about real conflicts.

## Working on mstack

```bash
make lint                 # every pre-commit hook on every file
make lint-rules           # check tests, full scan, contracts and guards
make lint-rules-changed   # the same, but the scan covers only changed files and warnings fail
make test                 # pytest
make demo                 # scans fixtures/invalid/, which must fail
```

Each rule ends with a `## Checks` section naming its checks, and each check points back to its rule through `metadata.source`. `make lint-rules` fails when:

- a check's own valid or invalid cases fail (`ast-grep test`), or the code breaks a check (`ast-grep scan`);
- an `.importlinter` contract is broken (`lint-imports`);
- a rule and its checks don't point to each other (`mstack coverage`);
- an `ast-grep-ignore` has no `rule-exception` with reason, expiry and approval (`mstack exceptions`):

  ```python
  # rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
  # ast-grep-ignore: no-manual-init-boilerplate
  ```

- rules or checks contain repo identifiers, URLs, emails or secrets (`mstack leak-check`).

`fixtures/valid/` is sample code that follows every rule; `fixtures/invalid/` breaks each one on purpose, and the tests prove every file there is still caught.

Planned work lives in [`docs/specs/`](docs/specs/README.md): one implementation plan per feature, grouped into now, next and future.

## CI and releases

`.github/workflows/ci.yml` runs `make lint`, `make lint-rules`, `make lint-rules-changed` (on pull requests) and `make test` on Python 3.12 and 3.13, plus pip-audit on the dependencies in `uv.lock`. `pr-title.yml` checks that PR titles follow [Conventional Commits](https://www.conventionalcommits.org/). To block merges on them, add both `Static checks` jobs as required status checks for `main`.

On every push to `main`, [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version, updates `CHANGELOG.md`, tags and publishes the release (`feat` is a minor bump, `fix` and `perf` a patch).
