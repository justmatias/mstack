# Implementation plan: rules-as-checks

A plan for Claude Code to execute. It builds a repo that turns team rules written in prose (`.cursor/rules`) into automated checks with ast-grep, plus three skills that keep both sides in sync.

**Before starting, Claude Code must read `docs/design.md`.** It holds the reasoning and the decisions already made; this plan does not repeat them.

## How to use this plan

- Execute the phases in order. Each one ends with verifiable acceptance criteria: do not move to the next phase until they pass.
- At least one commit per phase (`feat(phase-N): ...`).
- Anything marked **[VERIFY]** depends on external tools that may have changed. Confirm it against current documentation before implementing it; do not assume.
- If a decision is not covered here or in `docs/design.md`, pick the simplest option, record it in `docs/decisions.md`, and keep going.

## Cross-cutting principle 1: English only

**Everything in this repo, and everything the skills and scripts generate, is written in English. Never Spanish.** This applies to all phases and has priority over any other step in this plan.

- Code, identifiers, comments, docstrings, log and error messages.
- Prose rules (`.mdc`), YAML `message` and `note` fields, test cases, `docs/`, the README.
- Skills (`SKILL.md`, references, reviewer templates) and the replies the skills give.
- Commit messages, PR descriptions, issues opened by the skills, `rule-exception` reasons.

**When a source is not in English** (for example, an existing team rule written in Spanish), the skills read it as-is, but everything they generate from it is in English. `sync-rules` proposes translating non-English `.mdc` files as part of its sync plan; it never translates a team file without approval.

**Automated check:** `scripts/check_language.py` (see Phase 3) flags non-English text in generated artifacts. It is a heuristic: characters such as `ñ`, `¿`, `¡` and accented vowels, plus a ratio of common Spanish stopwords. The skills run it before proposing anything, and `make lint-rules` runs it over `lint-rules/`, `.cursor/rules/`, `skills/` and `docs/`.

## Cross-cutting principle 2: practices, not domain

The skills and scripts that generate or work with rules are used in work repos. **They extract coding practices, never domain or business information from the repo they run in.** This applies to all phases and all three skills, and has priority over any other step in this plan.

| May be extracted (practices) | Never extracted (domain) |
| --- | --- |
| Language constructs, libraries and frameworks (`@dataclass`, `requests`, `print`) | Business entities and names (classes, functions, modules, tables or fields named after the domain) |
| Patterns and anti-patterns (swallowed exceptions, verbose constructors) | Business rules, flows, calculations, thresholds or concrete values |
| Architecture in generic terms (`domain` does not import `infra`) | Names of clients, products, projects or teams |
| Naming, error-handling, logging and testing conventions | URLs, hosts, endpoints, emails, credentials or internal identifiers |
| Generic folder structure (`src/`, `tests/`, `domain/`) | Repo code snippets copied verbatim, data, or ticket contents |

**Operating rules for all skills:**
1. **Abstract before writing.** Every learning or mistake class is rewritten as a generic practice. If it cannot be expressed without the domain, it is dropped and reported as "dropped: domain-dependent".
2. **Synthetic tests.** Test cases (including `correct`'s "real past mistake") are rewritten as a minimal snippet with generic names (`Foo`, `Item`, `User`, `do_work`). They keep the *structure* of the mistake, never its content.
3. **Generic patterns.** YAML rules never match domain identifiers. The `files`/`ignores` of repo rules use only structural folders, never business-named modules. Personal rules contain no repo paths at all.
4. **Evidence by reference.** To justify a rule, cite a commit sha, a PR number or a transcript message index; never copy their content. Reviewer subagents may read the repo and transcripts, but return only abstracted findings.
5. **Automated verification.** Everything generated goes through `scripts/check_no_domain_leak.py` before it is proposed (see Phase 3). If the script flags something, the skill rewrites or drops it. It never ignores the finding.
6. **Transparency.** Each skill's reply lists what was abstracted and what was dropped as domain-dependent.

## Deliverables

1. `docs/design.md`: the design document (already included).
2. An example Python project with `.cursor/rules` rules and real checks that show the full loop.
3. Integration: Makefile, pre-commit, GitHub Actions, and agent hooks (Claude Code and Cursor).
4. Three skills, portable across Claude Code and Cursor:
   - **`sync-rules`**: discovers the team's rules in the environment and syncs them with `lint-rules/`, in both directions.
   - **`reflect-rules`**: from a chat, creates or updates rules in `.cursor/rules` together with their checks. Adapted from pstack's `reflect`.
   - **`correct-rules`**: analyzes the repo, finds mistakes that keep repeating, and makes them impossible at the highest enforcement level available. Adapted from pstack's `correct`.
5. **Personal user-level rules** (Phase 7): your own set of checks, defined once in `~/.config/my-rules/`. It applies in every repo you work in, writes nothing to those repos, is shared with no one, and coexists with each repo's own rules.

## Final repo layout

```
rules-as-checks/
├── README.md
├── PLAN.md
├── Makefile
├── pyproject.toml                    # uv; dev deps: ast-grep-cli, import-linter, pytest, pydantic, pyyaml
├── .importlinter                     # architecture contracts
├── .pre-commit-config.yaml
├── .github/workflows/lint-rules.yml
├── .claude/
│   ├── settings.json                 # PostToolUse hook
│   └── skills/                       # symlinks to skills/ (created by the install script)
├── .cursor/
│   ├── rules/                        # SOURCE OF TRUTH (prose)
│   │   ├── python-models.mdc
│   │   ├── logging.mdc
│   │   ├── error-handling.mdc
│   │   ├── architecture-layers.mdc
│   │   └── naming.mdc                # judgment rule (no check)
│   ├── hooks.json                    # [VERIFY] Cursor hooks
│   └── skills/                       # symlinks to skills/
├── docs/
│   ├── design.md
│   ├── decisions.md
│   └── rules-table.md                # generated: rule → what enforces it
├── lint-rules/
│   ├── sgconfig.yml
│   ├── rules/*.yml
│   └── rule-tests/*-test.yml
├── fixtures/
│   ├── valid/                        # "healthy" code: the scan passes
│   │   ├── domain/
│   │   ├── infra/
│   │   └── api/
│   └── invalid/<rule>/               # deliberate mistakes, one folder per .mdc rule: the scan MUST fail
├── scripts/
│   ├── check_rule_coverage.py
│   ├── check_exceptions.py
│   ├── check_no_domain_leak.py       # principle 2: no domain information in generated output
│   ├── check_language.py             # principle 1: generated output is English only
│   ├── generic_names.txt             # allowlist for check_no_domain_leak.py
│   ├── rules_table.py
│   ├── changed_files.sh
│   ├── install_skills.sh
│   ├── install_user_rules.sh         # Phase 7: installs the personal set and global hooks
│   ├── uninstall_user_rules.sh       # Phase 7: reverts all of the above
│   └── hooks/
│       ├── claude_post_edit.sh
│       └── cursor_after_edit.sh
├── user-level/                       # Phase 7: template for ~/.config/my-rules/
│   ├── sgconfig.yml
│   ├── rules/
│   ├── rule-tests/
│   ├── ignore-paths.txt
│   └── bin/
│       ├── my-rules-check            # single command for the personal set
│       ├── claude-post-edit          # Claude Code hook (user level)
│       ├── cursor-after-edit         # Cursor hook (user level)
│       └── git-hook-chain            # global git hook that chains to each repo's hooks
└── skills/
    ├── THIRD_PARTY_NOTICES.md        # MIT attribution for pstack
    ├── sync-rules/
    │   ├── SKILL.md
    │   └── references/
    │       ├── rule-format.md        # .mdc format + Checks section + metadata
    │       ├── authoring-a-check.md  # how to write YAML + tests + severity
    │       └── discovery.md          # where rules live in each environment
    ├── reflect-rules/
    │   ├── SKILL.md
    │   └── references/               # reviewer templates, adapted from pstack
    └── correct-rules/
        └── SKILL.md
```

---

## Phase 0: Bootstrap

1. `git init`, a Python `.gitignore`, and `pyproject.toml` managed with `uv`. Dev dependencies: `ast-grep-cli`, `import-linter`, `pytest`, `pyyaml`. App dependency: `pydantic`.
2. Keep `docs/design.md` (already present) and create an empty `docs/decisions.md` with a header.
3. A short `README.md`: what this is, `make setup`, `make lint-rules` and `make demo`, with a link to `docs/design.md`.
4. A `Makefile` with these targets (they may start empty):
   - `setup`: `uv sync`, `pre-commit install` and `scripts/install_skills.sh`.
   - `lint-rules`: the single command (see Phase 3). **Hooks, pre-commit and CI call this target and nothing else.**
   - `lint-rules-changed`: the same, only over files changed relative to `origin/main`.
   - `demo`: runs the scan over `fixtures/invalid/` and **expects it to fail**.
   - `rules-table`: regenerates `docs/rules-table.md`.

**Acceptance:** `make setup` runs cleanly and `ast-grep --version` works inside the environment.

## Phase 1: Example project and prose rules

1. `fixtures/valid/` with three minimal layers:
   - `domain/` with Pydantic models and pure logic.
   - `infra/` with an in-memory repository and logging.
   - `api/` with one orchestrating function.

   About 100 lines in total. It must pass every rule.
2. `fixtures/invalid/<rule>/`: one folder per `.mdc` rule, with one file per check holding the concrete violation (plus a variant per file where relevant). Examples: `logging/print_debug.py`, `error-handling/bare_except.py` and `architecture-layers/domain_imports_infra.py`.
3. Write the rules in `.cursor/rules/` with Cursor frontmatter (`description`, `globs`, `alwaysApply`) **[VERIFY the current .mdc format]**. Each ends with its `## Checks` section, in the format from `docs/design.md`:

| File | Prose rule | Type | Check |
| --- | --- | --- | --- |
| `python-models.mdc` | Prefer `pydantic.BaseModel` (`@dataclass` allowed when required); no classes whose `__init__` only assigns attributes | Pattern | `no-manual-init-boilerplate` |
| `logging.mdc` | No `print` in `fixtures/valid/`; use `logging.getLogger(__name__)` | Pattern | `no-print-in-app` |
| `error-handling.mdc` | No untyped `except:` and no `except Exception: pass` | Pattern | `no-bare-except`, `no-swallowed-exception` |
| `architecture-layers.mdc` | `domain` does not import from `infra` or `api` | Architecture | import-linter contract `domain-is-pure` |
| `naming.mdc` | Descriptive names; single-purpose functions | Judgment | `enforcement: llm-review` |

**Acceptance:** the 5 rules exist with their Checks section, and the example and demo code cover every case.

## Phase 2: Example checks with ast-grep and import-linter

1. `lint-rules/sgconfig.yml` with `ruleDirs` and `testConfigs`, as in `docs/design.md`.
2. One YAML per check in `lint-rules/rules/`. All of them have `id`, `language: Python`, `severity`, `message` (what to use instead), `note` (why), `metadata.source` (path to the `.mdc`) and, where useful, `files` / `ignores` for scope.
   - `no-print-in-app`: `pattern: print($$$ARGS)`, scoped to `fixtures/valid/**`.
   - `no-bare-except`: an `except_clause` without a type. **[VERIFY the node names with `ast-grep run --debug-query`]**.
   - `no-swallowed-exception`: `except Exception:` whose body is only `pass`.
   - `no-manual-init-boilerplate`: a class whose `__init__` only contains `self.$A = $A`. This is the hardest one. If ast-grep cannot express it well, record it in `docs/decisions.md` as a Fixit candidate, ship it as `warning`, or drop it. Do not force it at the cost of false positives.
3. One test per check in `lint-rules/rule-tests/<id>-test.yml`: at least 2 `valid` and 2 `invalid` cases. **One of the invalid cases must be the same code as in `fixtures/invalid/`**, following `correct`'s principle that every check must fail on a real mistake.
4. `.importlinter` with the `domain-is-pure` contract: `fixtures.valid.domain` does not import `fixtures.valid.infra` or `fixtures.valid.api`.
5. Run `ast-grep test -c lint-rules/sgconfig.yml` and iterate until everything passes.

**Acceptance:**
- `ast-grep test` passes.
- `ast-grep scan` over `fixtures/valid/` reports 0 errors.
- Over `fixtures/invalid/` it reports at least one violation per file.
- `lint-imports` passes on `fixtures/valid` and fails if `fixtures/invalid/architecture-layers/domain_imports_infra.py` is placed inside `domain/`. Test this with a test that copies the file in temporarily.

## Phase 3: Traceability, exceptions, guards and the single command

1. `scripts/check_rule_coverage.py` (Python, with `pyyaml`). Fails if:
   - an `.mdc` has no `## Checks` section;
   - an `enforced-by: <id>` has no YAML (nor an import-linter contract with that name);
   - a YAML has a `metadata.source` that does not exist;
   - a YAML is not listed in the `.mdc` named by its `metadata.source`.

   With `--json`, it outputs the drift report as JSON, which `sync-rules` consumes.
2. `scripts/check_exceptions.py`. Exceptions follow `correct`'s format: reason, expiry and human approval. Convention:
   ```python
   # rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
   # ast-grep-ignore: no-print-in-app
   ```
   The script fails if an `ast-grep-ignore` has no `rule-exception` directly above it, if a field is missing, or if `expires` is in the past. **[VERIFY the exact `ast-grep-ignore` syntax for Python]**.
3. `scripts/rules_table.py`: generates `docs/rules-table.md` (rule → check → severity → active exceptions) and inserts it between `<!-- rules-table:start -->` / `<!-- rules-table:end -->` markers in `CLAUDE.md` / `AGENTS.md`, if they exist. This is `correct`'s "rule table", generated instead of maintained by hand.
4. `scripts/changed_files.sh`: lists the `.py` files changed relative to `origin/main` (or the staged files in pre-commit).
5. `scripts/check_no_domain_leak.py <generated files> --repo <path>`: a heuristic for principle 2.
   - Collects the analyzed repo's own identifiers: names of the project's classes, functions, modules and packages, plus long string literals. Uses Python's `ast` module.
   - Discards standard-library names, third-party dependency names, and a generic allowlist (`Foo`, `Item`, `User`, `main`, `config`, etc.) kept in `scripts/generic_names.txt`.
   - Flags any match in the generated files (YAML, tests, `.mdc`), along with URLs, hosts, emails and strings that look like secrets.
   - Exits non-zero if it finds anything, listing each finding with file and line.

   It is a safety net, not a replacement for operating rule 1: it can produce false positives, and the skill decides how to rewrite. Test it by feeding it a generated YAML that deliberately includes a name from `fixtures/valid`.
6. `scripts/check_language.py <files>`: a heuristic for principle 1. It flags lines with Spanish-specific characters (`ñ`, `¿`, `¡`, accented vowels) and files whose ratio of common Spanish stopwords exceeds a threshold. It exits non-zero with file and line for each finding. Test it with one Spanish `.mdc` (must fail) and the repo's English rules (must pass).
7. `make lint-rules` runs, in order:
   - `ast-grep test`;
   - `ast-grep scan`;
   - `lint-imports`;
   - `check_rule_coverage.py`;
   - `check_exceptions.py`;
   - `check_no_domain_leak.py` over `lint-rules/` and `.cursor/rules/`;
   - `check_language.py` over `lint-rules/`, `.cursor/rules/`, `skills/` and `docs/`.

   It exits non-zero if anything fails.
8. `make lint-rules-changed` runs the same, but the `scan` only covers changed files. A common legacy pattern in the repo then does not block someone who did not touch it; only new or modified code fails. This is `correct`'s principle of "fail only when a change adds new instances".

**Acceptance:**
- `make lint-rules` passes.
- Deleting an `enforced-by` line makes the coverage check fail.
- An `ast-grep-ignore` without justification, or with an expired one, makes the exceptions check fail.
- `make rules-table` produces the table.
- `check_no_domain_leak.py` catches a `fixtures/valid` name inserted on purpose into a YAML, and passes on the example YAMLs.
- `check_language.py` fails on a Spanish `.mdc` and passes on the repo's rules.

## Phase 4: Integration (pre-commit, CI and agent hooks)

1. **pre-commit**: use `repo: local` hooks that call `make lint-rules-changed`, so pre-commit and CI run the same thing. Optionally add `boidolr/ast-grep-pre-commit` **[VERIFY the current version]**.
2. **GitHub Actions** (`.github/workflows/lint-rules.yml`), with three jobs:
   - `rules`: `make lint-rules-changed` on `pull_request` and `make lint-rules` on `push` to `main`.
   - `demo-must-fail`: runs `make demo` and **fails if the scan finds no violations**. It proves the checks still catch the real mistakes.
   - `sync-drift`: runs `check_rule_coverage.py`, so a new `.mdc` with neither checks nor an `llm-review` mark does not pass.

   Document in the README how to make `rules` a required check with branch protection.
3. **Claude Code hook** (`.claude/settings.json`): `PostToolUse` with matcher `Edit|Write|MultiEdit`, running `scripts/hooks/claude_post_edit.sh`. The script reads the JSON from stdin, extracts `tool_input.file_path` and, for `.py` files, runs `ast-grep scan -c lint-rules/sgconfig.yml <file>`. On errors, it prints them to stderr and exits with code 2, so Claude sees and fixes them. **[VERIFY the current Claude Code hooks schema]**.
4. **Cursor hook** (`.cursor/hooks.json`): the equivalent using `afterFileEdit` and `scripts/hooks/cursor_after_edit.sh`. **[VERIFY that the hook exists and whether its output reaches the agent]**. If it does not, record that in `docs/decisions.md` and fall back to an `alwaysApply` `.mdc` rule asking the agent to run `make lint-rules-changed` before finishing.

**Acceptance:**
- A commit with a `print` in `fixtures/valid/` is rejected by pre-commit.
- The workflow passes on a clean PR and fails on one with a violation (test with `act` if available; otherwise document it).
- Editing a file with Claude Code to introduce a `print` triggers the hook and shows the rule's message.

## Phase 5: Skills

### 5.0 Common base

1. **Fetch the pstack originals**: `git clone --depth 1 https://github.com/cursor/plugins /tmp/cursor-plugins` and read:
   - `pstack/skills/reflect/SKILL.md` and its `references/` (the reviewer templates);
   - `pstack/skills/correct/SKILL.md`;
   - pstack's Claude Code adapter, which maps Cursor names to Claude Code (transcripts, subagents).

   **[VERIFY the paths: the layout may have changed]**. The adaptations **start from the original text** and extend it. Do not rewrite them from memory.
2. `skills/THIRD_PARTY_NOTICES.md`: pstack's MIT license (Lauren Tan / Cursor), which files derive from which, and the date and commit of the copy. At the end of each adapted SKILL.md, one line: `Adapted from pstack/<skill> (MIT). See THIRD_PARTY_NOTICES.md`.
3. Shared references in `skills/sync-rules/references/`. The other two skills cite them by relative path, `../sync-rules/references/...`, which is why all three are always installed together:
   - `rule-format.md`: `.mdc` frontmatter, the `## Checks` section (`enforced-by:` / `enforcement: llm-review`), `metadata.source` and the exception format.
   - `authoring-a-check.md`: the recipe for a new check. Step by step:
     - pick the tool (ast-grep → import-linter → Fixit);
     - write the YAML;
     - write the tests, with an invalid case based on a real mistake (find it with `git log -S` if one exists), **rewritten as a synthetic snippet with generic names** (see principle 2);
     - run `ast-grep test`;
     - run `scan` to measure existing violations;
     - pick the severity (`error` if there are 0 violations or they are fixed in the same change; otherwise `warning` plus a migration issue);
     - update the Checks section;
     - run `check_no_domain_leak.py` and `check_language.py` over everything generated;
     - run `make lint-rules` and `make rules-table`.
   - `discovery.md`: where rules live in each environment (see `sync-rules`).
4. Every SKILL.md and reference, including the reviewer and synthesizer templates, states both cross-cutting principles near the top: English only, and practices not domain.
5. `scripts/install_skills.sh`: symlinks `skills/*` into `.claude/skills/` and `.cursor/skills/` **[VERIFY Cursor's skills path]**. With `--global`, it symlinks into `~/.claude/skills/`. It is idempotent.
6. Frontmatter of each SKILL.md: `name` and `description` (when to use it, with the phrases that trigger it). For `reflect-rules` and `correct-rules`, `disable-model-invocation: true`, as in pstack: they run on request because they change rules that affect everyone.

### 5.1 `sync-rules`: sync the environment's rules with the checks

**When:** "sync the rules", after editing `.cursor/rules`, when adopting the tool in an existing repo, or from CI in `--check` mode.

**Steps:**
1. **Discover** the team's rules in the environment, following `discovery.md`. By default, only repo rules:
   - `.cursor/rules/**/*.mdc` and the legacy `.cursorrules`;
   - `AGENTS.md` and `CLAUDE.md` (and `.claude/rules/` if it exists);
   - `.github/copilot-instructions.md`.

   User rules (`~/.cursor/rules`, `~/.claude/CLAUDE.md`) are read only on request, and never copied into the repo without confirmation: they are personal.
2. **Inventory**: split each file into atomic rules (one verifiable statement per item) and record the file and line of each one.
3. **Classify** each rule: pattern, architecture or judgment. For borderline cases, the examples table in `docs/design.md` decides.
4. **Compute drift** with `check_rule_coverage.py --json`, plus a semantic comparison: does the YAML still enforce what the `.mdc` says? Categories:
   - `new`: a checkable rule with no check;
   - `stale`: the rule changed and the check did not;
   - `orphan`: a YAML with no `.mdc`;
   - `judgment-unmarked`;
   - `non-english`: the prose rule is not in English;
   - `ok`.
5. **Show the sync plan** as a table (rule → action → files) and **wait for approval**. Exception: in `--check` mode it writes nothing and exits non-zero if there is drift.
6. **Apply** what was approved:
   - `new` and `stale`: follow `authoring-a-check.md`.
   - `orphan`: propose writing the rule in prose in the matching `.mdc` (reverse sync: YAML → `.cursor/rules`), or deleting the check.
   - `judgment-unmarked`: add `enforcement: llm-review`.
   - `non-english`: propose an English translation of the `.mdc`, keeping its meaning; apply it only if approved.
   - Rules that came from `AGENTS.md` / `CLAUDE.md` and have no `.mdc`: propose moving or copying them into `.cursor/rules`, so there is a single source of truth.
7. **Verify**: run `make lint-rules` and `make demo`, and regenerate `make rules-table`.
8. **Reply** with a short list: checks created, updated and deleted; rules marked as judgment; translations; existing violations and the severity chosen; and anything left pending.

**Properties:** idempotent (running it twice in a row changes nothing), and one commit per synced rule.

**`--user` mode** (see Phase 7): the same procedure, but between the user's prose rules (`~/.cursor/rules/*.mdc` and `~/.claude/CLAUDE.md`) and `~/.config/my-rules/`. In this mode it:
- never touches the current repo;
- prefixes check ids with `my-`;
- reports contradictions between your personal rules and the rules of the repo you are in. On conflict the repo wins: the skill proposes adding that repo to `ignore-paths.txt` for that rule, and never edits the repo's rules.

Commits go to the `~/.config/my-rules/` repo, if it is a git repo.

### 5.2 `reflect-rules`: from a chat to rules and checks (adapted from pstack `reflect`)

**What it keeps from `reflect`:**
- locating the transcript (Claude Code: `~/.claude/projects/<project>/<session>.jsonl`; Cursor: the agent-transcripts folder; with no transcript, a digest of the session);
- the parallel reviewers, which do not write files;
- the synthesizer with Accepted / Rejected / Backlog;
- the **approval gate**: nothing is applied without an explicit OK;
- routing workflow improvements to skill edits, as in the original.

**What changes (the superpowers):**
1. **A new reviewer focus.** A *coding conventions* lens is added to the original ones: the user's corrections on how to write code ("don't use dataclass", "use httpx here"), repeated preferences, and architecture decisions made in the chat. Each finding cites the transcript message index without copying its content. The reviewer and synthesizer templates include both cross-cutting principles: the synthesizer rejects, with reason "domain", any finding that cannot be expressed as a generic practice.
2. **The structural check is replaced.** The original sends to Backlog anything better enforced by a lint. Here, those items are classified (pattern, architecture or judgment) and turned, on the spot, into:
   - the prose rule, new or as an edit to an existing `.mdc` (look for a related rule first, to avoid duplicates);
   - its check, following `authoring-a-check.md`, with a synthetic invalid case that reproduces the structure of the chat's code, never the code itself.

   Only what truly cannot be checked with any available tool, or what requires a large architecture change, goes to Backlog.
3. **Conflict detection.** If a learning contradicts an existing rule, the proposal shows both side by side and asks for a decision; it never resolves the conflict on its own.
4. **Configurable cost.** By default, parallel reviewers as in pstack; with `--light`, a single reviewer plus the synthesizer. If `~/.cursor/rules/pstack-models.mdc` exists, honor its per-role models, as pstack does.
5. **Destination of each rule: repo or personal.** In the proposal, each new rule carries a suggested destination:
   - **repo**, if the correction is a team convention or the repo already has rules on that topic;
   - **personal**, if it is your own preference or the repo is not yours.

   You confirm or change the destination before anything is applied. The personal destination writes to `~/.cursor/rules/` and `~/.config/my-rules/` using the `sync-rules --user` procedure.

**Reply:** rules created or edited (path and a one-line change), checks created (id and severity), skill edits, backlog, and dropped findings with their reason.

### 5.3 `correct-rules`: repeated mistakes → impossible (adapted from pstack `correct`)

**What it keeps from `correct`:**
- finding mistake classes in recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds;
- a class counts from 2 occurrences;
- **enforcement levels, highest first**: architecture → types and lints → tests → docs and agent rules;
- one commit per class, starting with the most frequent;
- showing that each new check fails on a real past mistake;
- the same command locally and in CI;
- exceptions with reason, expiry and approval;
- the per-class reply, with evidence, the level chosen, and why a higher level did not work.

**What changes (the superpowers):**
1. **More evidence sources:**
   - PR review comments via `gh` (`gh pr list --state merged`, `gh api .../comments`);
   - existing `ast-grep-ignore` exceptions: many exceptions to the same rule mean the rule is wrong or an architecture change is missing;
   - accumulated `warning` findings;
   - optionally, recent agent transcripts.
2. **The "types and lints" level is concrete**: ast-grep for patterns, import-linter for module dependencies, Fixit when logic is needed. Always following `authoring-a-check.md`. The invalid case is based on the real commit (`git show <sha>`) but rewritten as synthetic code; the evidence cites the sha, not its content.
3. **Practice mistakes only.** A mistake class that is a business-logic bug ("the discount was computed wrong") produces no rule: it is reported as "dropped: domain-dependent". It only counts if a generic practice sits underneath, for example "money computed with `float` instead of `Decimal`".
4. **Always leaves a prose trail, at every level.** Even when the fix is architectural or a lint, the `.mdc` is created or updated with the "why" and its Checks section. The written rule stays as source of truth and index, and is shortened rather than deleted once the check covers it. This is a deliberate difference from `correct`, which deletes the rule once the mistake can no longer happen.
5. **Existing instances:** if the pattern is common in the repo, the rule ships as `warning` for the full scan but fails in `make lint-rules-changed` (new or touched code only), and a migration issue is opened.
6. **A manually corrected mistake that already has a rule without a check** is treated as a repeat and raised to the highest level in the same change, as `correct` prescribes.
7. **Personal destination as an alternative.** By default, fixes go to the repo. If you cannot change the repo, or the mistake class is yours (it appears only in your commits), it offers to move the check to your personal set. In that case it stays at the lint level only, because architecture and tests live in the repo and require changing it.

**Reply:** for each class, the evidence (commits or PRs), the level chosen, why not a higher one, the files touched, and the severity.

**Phase 5 acceptance:**
- `install_skills.sh` creates the symlinks in both environments.
- All three skills have valid frontmatter and descriptions that trigger on the expected phrases.
- `THIRD_PARTY_NOTICES.md` exists and every adapted skill references it.
- `check_language.py` passes over `skills/`.

## Phase 6: End-to-end tests

Run each scenario and record the result in `docs/e2e-results.md`:

1. **sync-rules, new rule**: add `.cursor/rules/http-client.mdc` ("use `httpx`, not `requests`") and an invalid fixture that uses `requests`. Run `sync-rules`. Expected: a new YAML with tests, the Checks section updated, the demo caught, and `make lint-rules` green on `fixtures/valid/`.
2. **sync-rules, orphan**: create a YAML with no `.mdc`. Expected: the skill proposes writing the rule in prose.
3. **sync-rules `--check`**: with drift, it exits non-zero without writing anything.
4. **sync-rules, non-English rule**: add an `.mdc` written in Spanish. Expected: the generated check is entirely in English, and the skill proposes translating the `.mdc`.
5. **reflect-rules**: in a session, write code with `datetime.now()` and correct it ("always `datetime.now(tz=UTC)`"). Run `reflect-rules`. Expected: it proposes the `.mdc` and the check, waits for approval and, once approved, creates them with a synthetic invalid case.
6. **correct-rules**: seed the history with 2 commits fixing the same mistake (for example `except Exception: pass`) and one with a workaround comment. Expected: it detects the class, picks lint, the test fails on a synthetic version of the original code, and it leaves one commit with the rule, the check and the `.mdc`.
7. **Full loop**: pre-commit rejects the violation, the Claude Code hook shows it on edit, CI fails on a PR with a violation, and `demo-must-fail` passes.
8. **No domain leak**: add to `fixtures/valid` a module with invented business names (for example `InvoiceLedger` and `apply_partner_rebate`) containing a practice mistake (`except Exception: pass`). Run `correct-rules` and `reflect-rules`. Expected:
   - the generated rule talks only about the practice;
   - the tests use generic names;
   - `check_no_domain_leak.py` passes on the generated output;
   - a logic bug seeded in that module (a wrong calculation) shows up as "dropped: domain-dependent".

## Phase 7: Personal user-level rules

**Goal:** define your own set of checks once and have it apply in every repo you work in, without writing anything into those repos and without sharing it. CI is left out on purpose: it lives in each repo and belongs to the team, so the personal set warns (agent and commit) but does not block merges.

### 7.1 The personal folder

`scripts/install_user_rules.sh` copies the `user-level/` template to `$MY_RULES_HOME` (default `~/.config/my-rules/`). **Only if it does not exist**: it never overwrites an existing set. Contents:

- `sgconfig.yml`, `rules/` and `rule-tests/`, with 2 example rules prefixed `my-` (for example `my-no-print` and `my-no-bare-except`) and their tests.
- `ignore-paths.txt`: one glob per line, optionally followed by a rule id (`~/work/legacy-repo/** my-no-bare-except`). It replaces `ast-grep-ignore` for the personal set, because no comments are written into other people's repos.
- `bin/my-rules-check <files...>`, the single command for the personal set:
  - filters by the rules' languages;
  - drops anything matching `ignore-paths.txt`;
  - runs `ast-grep scan -c $MY_RULES_HOME/sgconfig.yml <files>` **[VERIFY that `ruleDirs` resolves relative to `sgconfig.yml`, not to the current directory]**;
  - with `--with-repo`, if the current repo has `lint-rules/sgconfig.yml`, also runs that set over the same files;
  - exits non-zero if either fails.
- **Always over specific files** (the edited one, or the staged ones), never the whole repo. That way, old mistakes you did not write never show up.
- Escape hatch: `MY_RULES_DISABLE=1` disables everything for a single command.
- Optional: `git init` in `$MY_RULES_HOME` to version your set in a private repo of your own. In that case, `ignore-paths.txt` goes into `.gitignore`, because it contains work repo paths. Only generic practices are versioned, per principle 2.
- `check_no_domain_leak.py` (against the repo you were working in) and `check_language.py` run over the personal set every time a skill modifies it.

### 7.2 Global hooks

`install_user_rules.sh` also installs them, with these properties:
- it **merges**, never overwrites (with `jq` for the JSON files);
- it makes a `*.bak-<date>` backup first;
- it is idempotent;
- it is reversible with `scripts/uninstall_user_rules.sh`.

1. **Claude Code**: adds to `~/.claude/settings.json` a `PostToolUse` with matcher `Edit|Write|MultiEdit` that runs `bin/claude-post-edit`. The script reads the JSON from stdin, runs `my-rules-check --with-repo <file_path>` and, on failure, prints to stderr and exits with code 2. If the repo already has its own project hook (Phase 4), it detects it so the repo set does not run twice: in that case the user hook runs only the personal set. **[VERIFY the hooks schema and how user and project hooks combine]**.
2. **Cursor**: adds to `~/.cursor/hooks.json` an `afterFileEdit` that runs `bin/cursor-after-edit`, with the same logic. **[VERIFY that Cursor supports user-level hooks and whether their output reaches the agent]**. If it does not, create `~/.cursor/rules/my-rules.mdc` with `alwaysApply: true`, asking the agent to run `my-rules-check` on the touched files before finishing.
3. **Git**: `git config --global core.hooksPath ~/.config/my-rules/githooks`. This **replaces the local hooks of every repo**, so they must be chained:
   - `bin/git-hook-chain` is a single script. `githooks/` holds a symlink named after **every** standard git hook (`pre-commit`, `commit-msg`, `pre-push`, `post-checkout`, etc.) pointing at it, so no existing hook breaks.
   - Only in `pre-commit` does it run `my-rules-check` over `git diff --cached --name-only --diff-filter=ACM`.
   - Then, for any hook, it chains to the repo's own:
     - if `.pre-commit-config.yaml` exists and `pre-commit` is installed: `pre-commit hook-impl` or `pre-commit run` with the matching stage **[VERIFY the correct invocation]**;
     - otherwise, if `$(git rev-parse --git-dir)/hooks/<name>` exists and is executable, it runs it with the same arguments and stdin;
     - it propagates the exit code.
   - **Pitfalls to document in the README:**
     - with a global `core.hooksPath`, `pre-commit install` refuses to install. That is why the chain calls pre-commit directly.
     - Repos using **husky** set `core.hooksPath` at repo level, which takes precedence over the global one. There the personal git hook does not run, and only the agent hooks remain.
     - The installer warns if a global `core.hooksPath` already exists and does not overwrite it without confirmation.

### 7.3 Skills in personal mode

The changes are already described in 5.1 (`sync-rules --user`), 5.2 (repo or personal destination in `reflect-rules`) and 5.3 (personal alternative in `correct-rules`). In addition:
- `install_skills.sh --global` installs the three skills into `~/.claude/skills/` (and Cursor's user-level path **[VERIFY]**), so they are available in any repo.
- `authoring-a-check.md` gains a "personal set" section: `my-` prefix, tests in `$MY_RULES_HOME/rule-tests/`, exceptions in `ignore-paths.txt`, and the Checks section in the `.mdc` under `~/.cursor/rules/`.
- `check_rule_coverage.py` accepts `--rules-dir` and `--config` to run over the personal set (`~/.cursor/rules` ↔ `$MY_RULES_HOME`).

### 7.4 Tests

Run in a temporary directory, with `HOME` pointing at a test folder so your real configuration is never touched:
1. Install twice in a row: the second run changes nothing. Uninstalling leaves everything as it was, including any previous `core.hooksPath`.
2. **Repo A, no hooks of its own**: a commit with a `print` in a staged file is rejected by `my-no-print`. An old `print` in an unstaged file is ignored.
3. **Repo B, with `.pre-commit-config.yaml`**: the personal rules run, then the repo's; if either fails, the commit is rejected.
4. **Repo C, with a local `commit-msg`**: the local hook still runs through the chain.
5. **Repo D, with husky**: it is documented that the personal git hook does not run, while the agent hooks do.
6. **`ignore-paths.txt`**: an ignored path reports nothing; the rest still reports.
7. **Claude Code**: editing any repo to introduce a bare `except:` triggers the user hook with `my-no-bare-except`'s message.
8. **`sync-rules --user`**: adding `~/.cursor/rules/my-http.mdc` generates `my-http-client` with its tests in `$MY_RULES_HOME`, without touching the current repo.
9. **`reflect-rules`**: a correction marked as a personal preference ends up in the personal set, and a team convention ends up in the repo.

**Acceptance:** all 9 scenarios pass and are recorded in `docs/e2e-results.md`.

## Things to verify before closing

- ast-grep syntax (Python node names, `ast-grep-ignore`, `files`/`ignores`) against the installed version.
- The Claude Code and Cursor hooks schemas, and Cursor's skills path.
- The current layout of `cursor/plugins/pstack` and its Claude Code adapter.
- That no skill writes outside the repo unasked. Exception: `--user` mode and the personal destination, which write only to `~/.cursor/rules/` and `$MY_RULES_HOME`, always with approval.
- That no part of the personal set writes into repos (no configs, no exception comments).
- That no generated artifact (YAML, tests, `.mdc`, skill replies) contains domain information: `check_no_domain_leak.py` passes over everything generated during the tests.
- That every file in the repo and every generated artifact is in English: `check_language.py` passes over the repo and over everything generated during the tests.
- How `ruleDirs` resolves when `-c` points outside the current directory.
- User-level hooks in Claude Code and Cursor, and how they coexist with project hooks.
- The correct way to invoke pre-commit from a chained hook, and the behavior with husky.
