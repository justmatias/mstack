# mstack

My stack for guiding AI coding agents: the skills, rules and checks I use to steer them while they write code, kept in one place, tested and versioned like any other code.

Agents follow what they are told and what is checked. So every rule that can be verified becomes an automated check (**rules as checks**), and conventions are enforced instead of re-flagged in code review.

**New here?** [`docs/workflow.md`](docs/workflow.md) walks through the whole workflow: setting up a machine, adopting rules as checks in a repo, and the daily loop.

## What's inside

| Folder | What it is |
| --- | --- |
| `rules/` | Guidance in prose (`.mdc`) for decisions automated checks leave open. |
| `lint/` | The checks that enforce those rules (ast-grep). |
| `skills/` | Agent skills, grouped by topic (`skills/<group>/<name>/`). Installed flat, one folder per skill. |
| `agents/` | Optional subagent definitions ([format and install behavior](docs/setup/agent-assets.md)). |
| `mcp/` | Optional MCP server definitions ([format and install behavior](docs/setup/agent-assets.md)). |
| `instructions/` | Optional global agent instructions ([format and install behavior](docs/setup/agent-assets.md)). |
| `settings/` | Claude Code and Cursor hook settings ([format and install behavior](docs/setup/agent-assets.md)). |
| `src/mstack/` | The `mstack` CLI: `mstack lint` and the guards the skills and `make` targets run. |

## Getting started

You need git, [`uv`](https://docs.astral.sh/uv/), and at least one of Claude Code, Cursor or Codex.

**1. Clone and run the setup.**

```bash
git clone https://github.com/justmatias/mstack
cd mstack
claude "set up mstack"
```

The setup skill lives in `.agents/skills/setup-mstack/`, the project skills folder Codex, Cursor and opencode load: there, run `/setup-mstack` (`$setup-mstack` in Codex). Claude Code only loads `.claude/skills/`, so it finds the skill through `CLAUDE.md`, which imports `AGENTS.md`; ask it to *"set up mstack"*. Any other agent that reads `AGENTS.md` works the same way. The agent installs the `mstack` CLI, asks which tools you use, compares every skill, rule and setting with what you already have, shows one plan, and asks only where your own setup differs. Anything it replaces is backed up to `<folder>/.mstack-backups/<timestamp>/`.

| You use | Skills and agents go to | Rules and instructions go to | MCP servers | Settings |
| --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/`, `~/.claude/agents/` | `~/.claude/rules/`, a managed block in `~/.claude/CLAUDE.md` | `claude mcp add-json --scope user` | merged into `~/.claude/settings.json` |
| Cursor | `~/.cursor/skills/`, `~/.cursor/agents/` | Cursor Settings → Rules (the skill prints them for you to paste) | merged into `~/.cursor/mcp.json` | merged into `~/.cursor/hooks.json` |
| Codex | `~/.agents/skills/`, `~/.codex/agents/` | a managed block in `~/.codex/AGENTS.md` | merged into `~/.codex/config.toml` | none |

When tools share a home, Cursor can use the skills from Claude Code or Codex and the agents from Claude Code. If all three share a home, doctor warns about the two skill copies Cursor can see. On WSL, Cursor reads the Windows profile, so setup gives Cursor its own copies. `mstack platform` prints the tool folders, including the `CODEX_HOME` override for `~/.codex`.

[Agent hooks](hooks/README.md) run checks after edits and at Claude Code stops, only in projects with `.mstack.toml`.

**2. Use the skills in your projects.** In a repo that has no checks yet, start with `mstack init` (`--dry-run` shows the plan): it scaffolds `.mstack.toml`, an ast-grep `sgconfig.yml` and the rules folder, and with `--pre-commit`, `--ci github` or `--makefile` the hooks, the workflow and the Makefile targets below.

Skills live in five groups, which setup flattens on install:

| Group | Skills |
| --- | --- |
| `toolkit/` | `sync`, `reflect`, `correct`, `integrate`, `repair` |
| `engineering/` | `diff-review`, `blast-radius`, `architect`, `tdd`, `declutter`, `no-comments`, `modernize`, `research` |
| `shipping/` | `open-pr`, `leave-pr-comments`, `review-loop`, `babysit-pr`, `full-send`, `full-stop`, `show-me-your-work` |
| `learning/` | `how`, `why`, `teach`, `show-me` |
| `productivity/` | `bro`, `unslop`, `sharpen`, `recall`, `ketchup`, `grill-me`, `handoff` |

| Skill | Use it to |
| --- | --- |
| `sync` | Adopt rules as checks in a repo: turn its prose rules (`.cursor/rules`, `AGENTS.md`, `CLAUDE.md`) into checks, and keep both in sync. |
| `reflect` | Turn the corrections and preferences from the current session into rules and checks. |
| `correct` | Find the mistakes that keep repeating in a repo and make each one impossible. |
| `integrate` | Bring skills or rules from a GitHub URL into `skills/` or `rules/`, merged into what already exists, with their license, credit and a check for each rule. |
| `diff-review` | Review a diff on two axes: the repo's rules (above all the `llm-review` ones no check covers) and the spec it was built from. |
| `blast-radius` | Find what a change could break outside its diff, and prove the one fact its safety rests on by running real code. |
| `open-pr` | Open a pull request that is fast to review: problem-first title and body, a visual summary, before and after evidence, and a merge-danger note (one-way or two-way door, blast radius). |
| `leave-pr-comments` | Leave comments on GitHub that say an agent wrote them on the user's behalf (a note callout naming the model and the user), written conclusion-first, checked for secrets, previewed, and verified after posting. |
| `review-loop` | Loop an independent reviewer over a change: pick the reviewer from the agents and CLIs available, answer each finding with the smallest fix or evidence-backed pushback, and stop on approval, a stuck dispute or a 3-round budget. |
| `babysit-pr` | Watch a pull request through CI and review with one watcher, verify each bot finding before acting, keep the PR small, and rebase when the base moves. |
| `full-send` | Take a task to a merged PR unattended: prove the change, run the review loop, open and babysit the PR, merge once the gate passes. Only when you say "full send". |
| `full-stop` | The same as `full-send`, but stop with the PR ready for you to merge and never merge it. Only when you say "full stop". |
| `show-me-your-work` | Keep an append-only decision log for unattended work, audit it against the transcript, and have another model flag what you should look at. |
| `declutter` | Simplify working code without changing what it does, one tested change at a time, following the repo's rules. |
| `modernize` | Bring an old pull request up to date and say honestly whether it should stay open: check what landed on the base since, pick MODERNIZE, REWORK or CLOSE, then rebase and push with `--force-with-lease`. |
| `architect` | Sketch types, signatures and module boundaries before code, compare two shapes, and pick the one with the clearest ownership. |
| `tdd` | Fix a bug test-first: a regression test that fails for the right reason, then the smallest fix, with before and after evidence. |
| `research` | Investigate a question against primary sources in a background agent and save the findings, with a source for each claim, as a Markdown file in the repo. |
| `bro` | Restate the last message in plain language, shorter and without jargon. |
| `how` | Explain how a part of the codebase works, from one read-only subagent, so you can change it with a clear mental model. |
| `why` | Answer why code is the way it is from its commits and PR discussions, citing what the authors wrote and marking inferences. |
| `teach` | Explain a change or subsystem plainly in one account, built on `how` and `why`. |
| `show-me` | Show the current topic visually: pseudocode, call or file trees, Mermaid, diffs, or one focused HTML page. |
| `unslop` | Cut AI tells from any writing, by numbered rules. |
| `sharpen` | Make a task deeper, not bigger, and rewrite the prompt to ask for it. |
| `recall` | Rebuild your recent working context from chats, git and the shared record, and return a short brief with the next move. |
| `ketchup` | Catch you up on what changed in this chat since your last message, and list every call waiting on you with a recommended pick. |
| `grill-me` | Interview you about a plan in rounds, with a recommended answer for each question, until every decision is settled. |
| `handoff` | Write a handoff document in the temp directory so a fresh agent can continue the work, with suggested skills and secrets redacted. |
| `no-comments` | Delete comments that should not exist with the `comment-sicko` subagent, fix the code that caused them, and offer to encode real constraints as types, tests or lints. |
| `repair` | Close the gaps `mstack doctor` reports: reinstall the CLI, update drifted skills and rules with a backup, and rerun doctor until it is clean. |

**3. Verify.** `mstack doctor` checks the tools, CLI, checkout, and installed skills and rules for the selected tools. Use `mstack doctor --tool codex` for Codex alone or a comma-separated list for a mix. It prints the fix for each problem and exits 1 on any error. Run `/repair` (`$repair` in Codex) to apply fixes. `--online` also compares with the latest release.

Use `mstack cleanup` to preview old backups and their sizes, and `mstack cleanup --apply` to prune them. Cleanup keeps the newest batch in each location and only prunes other batches older than 30 days.

**4. Update.** `git pull` in the checkout, then run the setup again. Copies that only mstack changed update with a backup; it asks before touching your own edits.

## Use the checks in another repo

Select the bundled check packs in the consumer repo's `.mstack.toml`:

```toml
packs = ["python-core", "testing"]
```

Run `mstack packs list` to see what the installed release provides, then run `mstack lint` from the consumer repo. Shared prose, check files and rule tests ship with mstack. Existing project checks can run alongside the packs. A repo can remove a pack or set `disable` and `severity` under `[pack_overrides]` to adjust individual checks.

For local defaults across repos, put the same `packs` list in `~/.config/mstack/config.toml` (or `$XDG_CONFIG_HOME/mstack/config.toml`). A repo list replaces it, including `packs = []`. In CI, select packs in the repo or pass `mstack lint --packs python-core testing`.

Use the same release locally and in CI to run the same checks. Upgrading mstack updates the selected packs. To run the checks on every commit, add the hooks to the repo's `.pre-commit-config.yaml`. Pre-commit installs mstack in its own environment:

```yaml
repos:
  - repo: https://github.com/justmatias/mstack
    rev: vX.Y.Z   # pin a release that includes packs, or a commit SHA
    hooks:
      - id: mstack-lint        # ast-grep scan of the staged files; warnings fail too
      - id: mstack-rules       # rule tests and coverage, when rules or checks change
      - id: mstack-exceptions  # every ast-grep-ignore has a rule-exception
      - id: mstack-domain-check  # rules and checks hold no repo details
      - id: mstack-imports     # .importlinter contracts
      - id: mstack-commit-msg  # Conventional Commits messages (commit-msg stage)
```

mstack does not scan for secrets: add the [gitleaks](https://github.com/gitleaks/gitleaks) hook for that, pinned to a release tag.

`mstack-commit-msg` runs at the `commit-msg` stage: add `default_install_hook_types: [pre-commit, commit-msg]` at the top of the file so `pre-commit install` installs it too.

`mstack-imports` needs the project importable: if its modules import third-party packages, list them under the hook's `additional_dependencies`, or leave the hook out and run `mstack lint --only imports` from the project's environment.

Add the mstack action as a step in any GitHub Actions workflow. Here is a standalone workflow example. The action runs the full scan, and on pull requests the changed-files scan where warnings fail too. It needs only `contents: read`, and the checkout must have the full history so the base branch exists:

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
      - uses: justmatias/mstack@vX.Y.Z   # a full tag or sha; the @v<major> tag follows the major's fixes
```

Inputs: `mode` (`full`, `changed` or `both`; default `both` on pull requests, `full` otherwise), `base-ref` (default `origin/<base branch>`), `mstack-version` (default the action's own ref, so CLI and action match), `python-version` and `working-directory`. Every release moves the `v<major>` tag. On other CI providers, run the same two commands: `uvx --from git+https://github.com/justmatias/mstack@<tag> mstack lint`, and on merge requests the same with `--changed --base-ref origin/<base branch>`.

## Working on mstack

```bash
make setup                # dev dependencies
uv run pre-commit install   # installs the pre-commit and the commit-msg hooks
make lint                 # every pre-commit hook on every file
make lint-rules           # mstack lint: check tests, full scan and guards
make lint-rules-changed   # mstack lint --changed: the scan covers only changed files and warnings fail
make test                 # pytest
make demo                 # scans fixtures/invalid/, which must fail
```

`mstack lint` runs the same steps in any repo, with the ast-grep and import-linter that ship with the CLI.

Prose rules use `## Checks` to declare how they are reviewed. An ast-grep check can stand alone or declare a link to a prose rule with `metadata.source`. `make lint-rules` fails when:

- a check's own valid or invalid cases fail (`ast-grep test`), or the code breaks a check (`ast-grep scan`);
- a prose rule lacks a valid Checks section or a declared source link is invalid (`mstack coverage`);
- an `ast-grep-ignore` has no `rule-exception` with reason, expiry and approval (`mstack exceptions`):

  ```python
  # rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
  # ast-grep-ignore: no-manual-init-boilerplate
  ```

- rules or checks contain repo identifiers, URLs, hosts or emails (`mstack domain-check`); secrets are gitleaks' job;
- a commit message doesn't follow Conventional Commits (`mstack commit-msg`, as a commit-msg hook and in CI for every commit of a pull request);
- a skill in `skills/` has a broken frontmatter, a name that doesn't match its folder, a broken relative link, or is missing the principles header or its upstream credit (`mstack skills-check`).

`fixtures/valid/` is sample code that follows every rule; `fixtures/invalid/` breaks each one on purpose, and the tests prove every file there is still caught.

Planned work lives in [`docs/specs/`](docs/specs/README.md): one implementation plan per feature, grouped into next and future.

## CI and releases

`.github/workflows/ci.yml` runs `make lint`, `make lint-rules`, `make lint-rules-changed` (on pull requests) and `make test` on Python 3.12 and 3.13, the action in `action.yml` on this repo, the tests and `mstack lint` on macOS and Windows, plus pip-audit on the dependencies in `uv.lock`. `pr-title.yml` checks that PR titles follow [Conventional Commits](https://www.conventionalcommits.org/). To block merges on them, add both `Static checks` jobs as required status checks for `main`.

On every push to `main`, [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version, updates `CHANGELOG.md`, tags and publishes the release (`feat` is a minor bump, `fix` and `perf` a patch), and moves the `v<major>` tag to it.
