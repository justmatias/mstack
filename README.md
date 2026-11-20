# mstack

My stack for guiding AI coding agents: the skills, rules and checks I use to steer them while they write code, kept in one place, tested and versioned like any other code.

Agents follow what they are told and what is checked. So every rule that can be verified becomes an automated check (**rules as checks**), and conventions are enforced instead of re-flagged in code review.

## What's inside

| Folder | What it is |
| --- | --- |
| `rules/` | Conventions in prose (`.mdc`), the source of truth agents read before writing code. |
| `lint/` | The checks that enforce those rules (ast-grep). |
| `skills/` | Agent skills that keep rules and checks in sync and turn corrections into new rules. |
| `agents/` | Subagent definitions. |
| `mcp/` | MCP servers, one per file, with `${VAR}` placeholders for secrets. |
| `instructions/` | Global instructions for every project (`global.md`). |
| `settings/` | A partial Claude Code `settings.json`: permissions, status line, env. |
| `src/mstack/` | The `mstack` CLI: `mstack lint` and the guards the skills and `make` targets run. |

## Getting started

You need [`uv`](https://docs.astral.sh/uv/), git, and Claude Code or Cursor.

**1. Clone and install the CLI.** The skills run the guards as `mstack <command>`, so it has to be on your `PATH`.

```bash
git clone https://github.com/justmatias/mstack
cd mstack
make setup                      # dev dependencies
uv tool install --editable .    # the mstack CLI; `mstack --help` lists the commands
```

**2. Install the skills, rules and agent config.** Open this repo in Claude Code or Cursor and ask the agent to *"set up mstack following skills/setup-mstack/SKILL.md"*. It asks which tool you use, compares each skill and rule with what you already have, and waits for your answer before every change.

| You use | Skills and agents go to | Rules and instructions go to | MCP servers | Settings |
| --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/`, `~/.claude/agents/` | `~/.claude/rules/`, a managed block in `~/.claude/CLAUDE.md` | `claude mcp add-json --scope user` | merged into `~/.claude/settings.json` |
| Cursor | `~/.cursor/skills/`, `~/.cursor/agents/` | Cursor Settings → Rules (the skill prints them for you to paste) | merged into `~/.cursor/mcp.json` | none |
| Both | `~/.claude/` only (Cursor loads it too) | both of the above | both of the above | merged into `~/.claude/settings.json` |

**Windows and WSL.** On native Windows, `~` is `%USERPROFILE%`. On WSL, Claude Code inside WSL uses the WSL home, but Cursor runs on Windows and reads the Windows profile (`/mnt/c/Users/<user>/.cursor`), so with both tools the skills and agents are copied to each home. `mstack platform` prints where each tool's files go (`MSTACK_WINDOWS_HOME` overrides the Windows profile when it can't be found).

Skills, rules and agents are copies, not symlinks. MCP servers, instructions and settings are merged: your own keys and text stay. Anything replaced is backed up to `<folder>/.mstack-backups/<timestamp>/`.

**3. Use the skills in your projects.** In a repo that has no checks yet, start with `mstack init` (`--dry-run` shows the plan): it scaffolds `.mstack.toml`, an ast-grep `sgconfig.yml` and the rules folder, and with `--pre-commit`, `--ci github` or `--makefile` the hooks, the workflow and the Makefile targets below.

| Skill | Use it to |
| --- | --- |
| `sync` | Adopt rules as checks in a repo: turn its prose rules (`.cursor/rules`, `AGENTS.md`, `CLAUDE.md`) into checks, and keep both in sync. |
| `reflect` | Turn the corrections and preferences from the current session into rules and checks. |
| `correct` | Find the mistakes that keep repeating in a repo and make each one impossible. |
| `integrate` | Bring skills or rules from a GitHub URL into `skills/` or `rules/`, merged into what already exists, with their license, credit and a check for each rule. |
| `review` | Review a diff on two axes: the repo's rules (above all the `llm-review` ones no check covers) and the spec it was built from. |

**4. Verify.** `mstack doctor` checks that this machine has everything: the tools, the CLI, the checkout, every skill and rule, and no drift from the checkout. It prints the fix for each problem and exits 1 on any error. `--online` also compares with the latest release.

**5. Update.** Pull this repo and run step 2 again. mstack records what it installed, so upstream changes update on their own (with a backup), your own edits are kept, and it only asks about real conflicts.

## Use the checks in another repo

`mstack lint` runs every check in any repo that has the layout (`.mstack.toml`, an ast-grep `sgconfig.yml`, the prose rules). To run them on every commit, add the hooks to that repo's `.pre-commit-config.yaml`. pre-commit installs mstack in its own environment, with ast-grep and import-linter, so the repo needs nothing else:

```yaml
repos:
  - repo: https://github.com/justmatias/mstack
    rev: vX.Y.Z   # pin a full release tag (or a commit sha), never a branch
    hooks:
      - id: mstack-lint        # ast-grep scan of the staged files; warnings fail too
      - id: mstack-rules       # rule tests and coverage, when rules or checks change
      - id: mstack-exceptions  # every ast-grep-ignore has a rule-exception
      - id: mstack-leak-check  # rules and checks hold no repo details
      - id: mstack-imports     # .importlinter contracts
      - id: mstack-commit-msg  # Conventional Commits messages (commit-msg stage)
```

`mstack-commit-msg` runs at the `commit-msg` stage: add `default_install_hook_types: [pre-commit, commit-msg]` at the top of the file so `pre-commit install` installs it too.

`mstack-imports` needs the project importable: if its modules import third-party packages, list them under the hook's `additional_dependencies`, or leave the hook out and run `mstack lint --only imports` from the project's environment.

In GitHub Actions, the action in `action.yml` runs the full scan, and on pull requests the changed-files scan where warnings fail too. It needs only `contents: read`, and the checkout must have the full history so the base branch exists:

```yaml
name: mstack
on: [push, pull_request]
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - uses: justmatias/mstack@vX.Y.Z   # a full tag or sha; @v3 follows the major's fixes
```

Inputs: `mode` (`full`, `changed` or `both`; default `both` on pull requests, `full` otherwise), `base-ref` (default `origin/<base branch>`), `mstack-version` (default the action's own ref, so CLI and action match), `python-version` and `working-directory`. Every release moves the `v<major>` tag. On other CI providers, run the same two commands: `uvx --from git+https://github.com/justmatias/mstack@<tag> mstack lint`, and on merge requests the same with `--changed --base-ref origin/<base branch>`.

## Working on mstack

```bash
uv run pre-commit install   # installs the pre-commit and the commit-msg hooks
make lint                 # every pre-commit hook on every file
make lint-rules           # mstack lint: check tests, full scan and guards
make lint-rules-changed   # mstack lint --changed: the scan covers only changed files and warnings fail
make test                 # pytest
make demo                 # scans fixtures/invalid/, which must fail
```

`mstack lint` runs the same steps in any repo, with the ast-grep and import-linter that ship with the CLI.

Each rule ends with a `## Checks` section naming its checks, and each check points back to its rule through `metadata.source`. `make lint-rules` fails when:

- a check's own valid or invalid cases fail (`ast-grep test`), or the code breaks a check (`ast-grep scan`);
- a rule and its checks don't point to each other (`mstack coverage`);
- an `ast-grep-ignore` has no `rule-exception` with reason, expiry and approval (`mstack exceptions`):

  ```python
  # rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
  # ast-grep-ignore: no-manual-init-boilerplate
  ```

- rules or checks contain repo identifiers, URLs, emails or secrets (`mstack leak-check`);
- a commit message doesn't follow Conventional Commits (`mstack commit-msg`, as a commit-msg hook and in CI for every commit of a pull request);
- a skill in `skills/` has a broken frontmatter, a name that doesn't match its folder, a broken relative link, or is missing the principles header or its upstream credit (`mstack skills-check`).

`fixtures/valid/` is sample code that follows every rule; `fixtures/invalid/` breaks each one on purpose, and the tests prove every file there is still caught.

Planned work lives in [`docs/specs/`](docs/specs/README.md): one implementation plan per feature, grouped into now, next and future.

## CI and releases

`.github/workflows/ci.yml` runs `make lint`, `make lint-rules`, `make lint-rules-changed` (on pull requests) and `make test` on Python 3.12 and 3.13, the action in `action.yml` on this repo, the tests and `mstack lint` on macOS and Windows, plus pip-audit on the dependencies in `uv.lock`. `pr-title.yml` checks that PR titles follow [Conventional Commits](https://www.conventionalcommits.org/). To block merges on them, add both `Static checks` jobs as required status checks for `main`.

On every push to `main`, [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version, updates `CHANGELOG.md`, tags and publishes the release (`feat` is a minor bump, `fix` and `perf` a patch), and moves the `v<major>` tag to it.
