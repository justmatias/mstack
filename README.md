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
| `settings/` | Hook settings for Claude Code, Cursor and Codex ([format and install behavior](docs/setup/agent-assets.md)). |
| `src/mstack/` | The `mstack` CLI, which installs this content and checks the machine: `doctor`, `platform`, `cleanup`, `render-rule`, `skills-check` and `rule-tests-check`. The checks run through [rulepack](https://github.com/justmatias/rulepack), which setup installs next to it. |

## Getting started

You need git, [`uv`](https://docs.astral.sh/uv/), and at least one of Claude Code, Cursor or Codex.

**1. Clone and run the setup.**

```bash
git clone https://github.com/justmatias/mstack
cd mstack
claude "set up mstack"
```

The setup skill lives in `.agents/skills/setup-mstack/`, the project skills folder Codex, Cursor and opencode load: there, run `/setup-mstack` (`$setup-mstack` in Codex). Claude Code only loads `.claude/skills/`, so it finds the skill through `CLAUDE.md`, which imports `AGENTS.md`; ask it to *"set up mstack"*. Any other agent that reads `AGENTS.md` works the same way. The agent installs the `mstack` and `rulepack` CLIs, asks which tools you use, compares every skill, rule and setting with what you already have, shows one plan, and asks only where your own setup differs. Anything it replaces is backed up to `<folder>/.mstack-backups/<timestamp>/`, and a rule beside its rules folder, where no tool loads it.

| You use | Skills and agents go to | Rules and instructions go to | MCP servers | Settings |
| --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills/`, `~/.claude/agents/` | `~/.claude/rules/`, a managed block in `~/.claude/CLAUDE.md` | `claude mcp add-json --scope user` | merged into `~/.claude/settings.json` |
| Cursor | `~/.cursor/skills/`, `~/.cursor/agents/` | Cursor Settings → Rules (the skill prints them for you to paste) | merged into `~/.cursor/mcp.json` | merged into `~/.cursor/hooks.json` |
| Codex | `~/.agents/skills/`, `~/.codex/agents/` | a managed block in `~/.codex/AGENTS.md` | merged into `~/.codex/config.toml` | merged into `~/.codex/hooks.json` |

When tools share a home, Cursor can use the skills from Claude Code or Codex and the agents from Claude Code. If all three share a home, doctor warns about the two skill copies Cursor can see. On WSL, Cursor reads the Windows profile, so setup gives Cursor its own copies. `mstack platform` prints the tool folders, including the `CODEX_HOME` override for `~/.codex`.

[Agent hooks](hooks/README.md) run checks after edits and at Claude Code and Codex stops, only in projects with `.rulepack.toml`. They run `rulepack hook`.

**2. Use the skills in your projects.** In a repo that has no checks yet, start with `rulepack init` (`--dry-run` shows the plan): it scaffolds `.rulepack.toml`, an ast-grep `sgconfig.yml` and the rules folder, and with `--pre-commit`, `--ci github` or `--makefile` the hooks, the workflow and the Makefile targets below.

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

Linting moved to [rulepack](https://github.com/justmatias/rulepack): `rulepack lint`, its pre-commit hooks and its GitHub Action run a repo's own checks, configured in `.rulepack.toml`. Its README documents them. To run mstack's checks, declare this repo as a source, pinned to a release tag, select its packs, and lock it:

```toml
packs = ["mstack/python-core", "mstack/testing"]

[sources.mstack]
git = "https://github.com/justmatias/mstack"
ref = "vX.Y.Z"
```

Then run `rulepack packs lock` and commit `rulepack.lock`. [`packs.toml`](packs.toml) lists each pack's checks.

**Moving to rulepack `v0.7.0`:** it no longer accepts `rules_dir`, `pre_commit_config`, `[domain_check]` or `[commits]` in `.rulepack.toml`, and the agent hooks stop with a config error until they are gone. Delete them. The coverage guard moved to mstack, and `rulepack lint`, its hooks and its GitHub Action no longer run it: call `mstack coverage` in your own CI step or Makefile target, with `--rules-dir` and `--pre-commit-config` when those files are not at `.cursor/rules/` and `.pre-commit-config.yaml`. The `exceptions`, `domain-check` and `commit-msg` guards are gone, so remove any CI step that runs them and the `rulepack-commit-msg` hook.

**Migrating from mstack `v6.x`:**

Every repo:

- Move `sgconfig`, `importlinter`, `[scan]`, `[hooks]` and `[changed]` from `.mstack.toml` to a new `.rulepack.toml`, and delete `.mstack.toml`. A `rules_dir` or `pre_commit_config` it set becomes a `mstack coverage` flag, as above. In `.pre-commit-config.yaml`, change `repo:` to `https://github.com/justmatias/rulepack`, pin a rulepack tag and rename the hook ids rulepack still ships from `mstack-*` to `rulepack-*`, also in any `enforced-by-hook:` line of the prose rules. Remove the commit-msg hook. Replace `uses: justmatias/mstack@...` with `uses: justmatias/rulepack@...` (the `mstack-version` input becomes `rulepack-version`). Rerun the mstack setup so the agent hooks run `rulepack hook`.

A repo that also selected packs (`packs = [...]`):

- Change `python-core` and `testing` to `mstack/python-core` and `mstack/testing`, and drop `git`, which had no checks and is gone.
- Add the `[sources.mstack]` block above, run `rulepack packs lock`, and commit `rulepack.lock`.

## Working on mstack

```bash
make setup                # dev dependencies
uv run pre-commit install   # installs the pre-commit hooks
make lint                 # every pre-commit hook on every file
make lint-rules           # rulepack lint: check tests, full scan and guards
make lint-rules-changed   # rulepack lint --changed: the scan covers only changed files and warnings fail
make test                 # pytest
```

The `rulepack` that lints this repo is a dev dependency, pinned in `pyproject.toml`. It brings ast-grep and import-linter.

Prose rules use `## Checks` to declare how they are reviewed. An ast-grep check can stand alone or declare a link to a prose rule with `metadata.source`. `make lint-rules` fails when:

- a check's own valid or invalid cases fail (`ast-grep test`), or the code breaks a check (`ast-grep scan`);
- a prose rule lacks a valid Checks section or a declared source link is invalid (`mstack coverage`);
- a skill in `skills/` has a broken frontmatter, a name that doesn't match its folder, a broken relative link, or is missing the principles header or its upstream credit (`mstack skills-check`);
- a check in `lint/rules/` has no rule test with both `valid` and `invalid` cases, a rule test names no check, or two checks share an id (`mstack rule-tests-check`). `ast-grep test` alone passes when a check has no test.

`fixtures/valid/` is sample code that follows every rule; `fixtures/invalid/` breaks each one on purpose, and the tests prove every file there is still caught.

Planned work lives in [`docs/specs/`](docs/specs/README.md): one implementation plan per feature, grouped into next and future.

## CI and releases

`.github/workflows/ci.yml` runs `make lint`, `make lint-rules`, `make lint-rules-changed` (on pull requests) and `make test` on Python 3.12 and 3.13, the tests and `rulepack lint` on macOS and Windows, plus pip-audit on the dependencies in `uv.lock`. `pr-title.yml` checks that PR titles follow [Conventional Commits](https://www.conventionalcommits.org/). To block merges on them, add both `Static checks` jobs as required status checks for `main`.

On every push to `main`, [python-semantic-release](https://python-semantic-release.readthedocs.io/) bumps the version, updates `CHANGELOG.md`, tags and publishes the release (`feat` is a minor bump, `fix` and `perf` a patch).
