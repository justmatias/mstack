# End-to-end results

Results of the acceptance scenarios, recorded while executing `PLAN.md`. Dates are 2026-11-19 unless stated.

Paths and check names are the ones in use when each scenario ran. The repo was restructured later (`example_app/` and `demo/violations/` became `fixtures/valid/` and `fixtures/invalid/`, scripts moved under `scripts/guards/`, and `prefer-pydantic-over-dataclass` was dropped); see `docs/decisions.md`.

## Phase 4: integration

| Scenario | Result | Evidence |
| --- | --- | --- |
| A commit with a `print` in `example_app/` is rejected by pre-commit | Pass | Hook `lint-rules` failed with `error[no-print-in-app]`; HEAD did not move. |
| Editing a file with Claude Code to introduce a `@dataclass` triggers the hook | Pass | Hook installed with `scripts/setup.py --with claude-hook`; a `Write` of a `@dataclass` into `example_app/domain/` returned `PostToolUse:Write hook blocking error` with `error[prefer-pydantic-over-dataclass]: Use pydantic.BaseModel instead of @dataclass`. |
| Cursor hook returns findings to the agent | Partial | Script tested with a sample `postToolUse` payload: returns `{"additional_context": "...prefer-pydantic-over-dataclass..."}`. Not run inside Cursor (not available on this machine). |
| Workflow passes on a clean PR and fails on one with a violation | Simulated | `act` is not installed. The `rules` job commands were run locally: `make lint-rules-changed` passes on the clean tree and fails with `error[no-print-in-app]` when an untracked `example_app/*.py` with a `print` is added. `make demo` and `check_rule_coverage.py` pass. |

## Phase 6: end-to-end scenarios

The skills were executed by the agent following their `SKILL.md`. Approval gates were answered by the agent acting for the user (the user asked not to be consulted on reversible decisions). Reviewer and synthesizer templates for `reflect-rules` were applied inline (`--light` shape, no subagents spawned) to keep the run cheap. Scenarios 2–6 and 8 ran in throwaway clones of the repo, so no seeded history, Spanish input or business-named code entered this repo.

| # | Scenario | Result | Evidence |
| --- | --- | --- | --- |
| 1 | sync-rules, new rule (`http-client.mdc`: httpx, not requests) | Pass | `check_rule_coverage.py --json` reported `missing-checks-section`; classified as pattern; created `prefer-httpx-over-requests` (3 valid, 4 invalid, one identical to `demo/violations/requests_client.py`); 0 existing violations → `error`; Checks section updated; `make demo` catches the demo file; `make lint-rules` green. `check_no_domain_leak.py` flagged a function name copied from the demo file (`fetch_status`), which was rewritten as `do_work`. Shipped in its own pull request (`rules/prefer-httpx-over-requests`). |
| 2 | sync-rules, orphan YAML (`no-eval` with no `metadata.source`) | Pass | Drift report: `orphan`. Proposed reverse sync: a new `code-execution.mdc` with the prose rule and `enforced-by: no-eval`, plus `metadata.source` in the YAML. After applying it, coverage is OK. |
| 3 | sync-rules `--check` with drift | Pass | `check_rule_coverage.py` exited 1; `git status --porcelain` was identical before and after (nothing written). |
| 4 | sync-rules, non-English rule (an `.mdc` written in Spanish about `assert`) | Pass | Categories: `missing-checks-section` + `non-english`. Generated `no-assert-in-app` (YAML, tests, demo file) entirely in English (no accented characters found). Proposed an English translation that keeps the meaning, and renaming the file to `assertions.mdc`; applied after approval. `check_no_domain_leak.py` flagged a string literal shared with the demo file; it was shortened. |
| 5 | reflect-rules: `datetime.now()` corrected to `datetime.now(tz=UTC)` | Pass | Session digest with the correction at message `#3` and `#5`. Conventions lens: one pattern finding, destination repo, no related rule. The business context (which model field) was abstracted away. Proposal (`datetimes.mdc` + `no-naive-datetime-now`) shown and approved, then created with a synthetic invalid case reproducing the structure of message `#2`. The scan found 1 existing violation (a naive timestamp in the setup CLI), fixed in the same change, so the rule shipped as `error`. |
| 6 | correct-rules: 2 fix commits for `except Exception: pass` + a workaround comment | Pass | Evidence: fix commits `b14c93c`, `1300f04` (seeded) and a workaround comment in an infra module; the prose rule existed with no check (a repeat). Level: lint (no dependency to cut, Python types cannot forbid it). The test suite fails without the rule (`1 test case(s) matched no rule`), and the check fails on the original code from `067f07e`. One commit with the rule, check and `.mdc`. |
| 7 | Full loop | Pass | Pre-commit rejects a staged `print` (Phase 4); the Claude Code hook shows `prefer-pydantic-over-dataclass` on edit (Phase 4); CI is simulated locally because `act` is unavailable (`make lint-rules-changed` fails on a violation); `make demo` passes because the scan fails on `demo/violations/`. |
| 8 | No domain leak (`InvoiceLedger.apply_partner_rebate` with `except Exception: pass` and a doubled-rebate bug) | Pass | correct-rules: class "broad exception swallowed" kept, 1 existing instance fixed in the same change; class "rebate applied twice" (`668cc1b`) reported as `dropped: domain-dependent` (money as `float` noted, below the 2-occurrence threshold). The generated rule, YAML and tests contain no business words, and `check_no_domain_leak.py --repo .` passes even though the repo now defines those names. Negative control: a test copied from the business module is flagged (`InvoiceLedger`, `apply_partner_rebate`). reflect-rules: the correction is `already-covered`; a business threshold from the same session is `dropped: domain-dependent`. |

## Phase 7: personal user-level rules

Every scenario ran with `HOME` pointing at a temporary folder and `GIT_CONFIG_GLOBAL` at a temporary file, so the real configuration was never touched. Scenarios 1–7 are automated in `tests/user_level/test_user_level.py` (`make test`); 8–10 are skill runs performed by the agent.

| # | Scenario | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Install twice; uninstall restores everything, including the previous `core.hooksPath` | Pass | `test_install_twice_then_uninstall_restores_everything`: the second install changes no file; after uninstall the temporary `HOME` is byte-identical (backups aside) and `core.hooksPath` is back to its previous value. Also: an existing `core.hooksPath` is kept without `--replace-hooks-path`, and an existing `$MY_RULES_HOME` is never overwritten. |
| 2 | Repo A, no hooks: staged `print` rejected; old `print` in an unstaged file ignored | Pass | `test_repository_without_hooks_rejects_staged_print`, `test_old_print_in_unstaged_file_is_ignored`. |
| 3 | Repo B with `.pre-commit-config.yaml`: personal rules then the repo's; either failing rejects the commit | Pass | `test_repository_with_pre_commit_runs_both` (personal fails, repo fails, both pass). |
| 4 | Repo C with a local `commit-msg`: still runs through the chain | Pass | `test_local_commit_msg_hook_still_runs`. |
| 5 | Repo D with husky: personal git hook does not run, agent hooks do | Pass (documented) | `test_husky_repository_bypasses_personal_git_hook`: the commit with a `print` succeeds; `claude-post-edit` on the same file exits 2 with `my-no-print`. README "Pitfalls of the global git hook". |
| 6 | `ignore-paths.txt`: an ignored path reports nothing, the rest still reports | Pass | `test_ignore_paths_silences_only_that_rule`; also `test_disable_variable_turns_everything_off`. |
| 7 | Claude Code: introducing a `@dataclass` triggers the user hook with `my-prefer-pydantic` | Pass | `test_claude_user_hook_reports_personal_and_repository_rules`; with a project hook present, only the personal set runs (`test_claude_user_hook_skips_repository_set_when_project_hook_exists`). The Cursor user hook returns `additional_context` (`test_cursor_user_hook_returns_additional_context`). |
| 8 | `sync-rules --user`: `~/.cursor/rules/my-http.mdc` → `my-http-client` in `$MY_RULES_HOME` | Pass | Drift `missing-checks-section`; generated `my-http-client` YAML and tests (all pass), Checks section added, personal coverage OK (14 rules), leak check OK, `my-rules-check` reports `error[my-http-client]` on a file importing `requests`. `git status` and `HEAD` of the current repo unchanged. |
| 9 | `reflect-rules`: personal preference → personal set; team convention → repo | Pass | Digest: message `#2` ("my own preference", f-strings) → `my-prefer-f-strings` in `$MY_RULES_HOME` + `~/.cursor/rules/my-prefer-f-strings.mdc`, repo untouched; message `#4` ("the team's layering") → related rule found (`architecture-layers.mdc`) and edited instead of duplicated, plus import-linter contract `infra-does-not-import-api`, which is `KEPT` on the code and `BROKEN` on a synthetic copy of message `#3`. A YAML quoting mistake (`: ` in `message`) was caught by `ast-grep test` and fixed. |
| 10 | `sync-rules --user --from-conventions` on a copy of the conventions store | Pass | 20 conventions, 0 malformed. Checkable: `my-no-test-classes`, `my-no-module-docstrings`, `my-imports-no-parent-relative`, `my-no-fixtures-in-test-modules` (warning), all tests passing. Judgment (`llm-review` `.mdc`): `avoid-unnecessary-indirection`, `no-abbreviations-in-names`, `logging-state-changing-ops`, `import-via-package-init-reexports`, `mcp-server-structure`, `per-test-module-folder-conftest`, `pytest-action-fixtures-underscore-usefixtures`, and the judgment half of `test-fixtures-conftest`. Skipped as tooling notes: the 5 `pylint-*`, 2 `ruff-*` and `hookpin-stub-only-deps`. Non-code: `conventional-commits`, a `commit-msg` regex step for `git-hook-chain` proposed but not applied (pending approval). Project names in conventions (a repo and module mentioned as evidence) were not carried over; leak check OK. The store copy is byte-for-byte unchanged; a second run finds every `derived-sha256` current (nothing to do); appending a line to one convention makes only `my-no-test-classes.mdc` `stale`; deleting one makes only its `.mdc` `orphan`. |

## Things to verify before closing

| Item | Result |
| --- | --- |
| ast-grep syntax (Python node names, `ast-grep-ignore`, `files`/`ignores`) | Verified with ast-grep 0.51.3: decisions 6, 8, 12, 30. |
| Claude Code and Cursor hook schemas; Cursor's skills path | Decisions 19, 20, 24, 31. |
| Layout of `cursor/plugins/pstack` and its Claude Code adapter | Decision 23. |
| No skill writes outside the repo unasked | Only `--user` mode and the personal destination write outside, to `~/.cursor/rules/` and `$MY_RULES_HOME`, after approval (scenarios 8–10 checked the repo is untouched). |
| No part of the personal set writes into repos | Exceptions live in `ignore-paths.txt`; the hooks only read. Scenarios 2–7 leave no files in the test repos beyond what the tests commit. |
| No generated artifact contains domain information | `check_no_domain_leak.py` passed over every generated file in Phases 6–7 (two real findings in scenario 1 and 4 were rewritten). |
| Every file and generated artifact is in English | Enforced as an explicit instruction in every skill (decision 16); reviewed by hand for this repo and the generated files. The only non-English text was scenario 4's input, kept in a throwaway clone. |
| How `ruleDirs` resolves when `-c` points outside the current directory | Relative to the config file (decision 34). |
| User-level hooks and their coexistence with project hooks | Decision 31; scenario 7. |
| Invoking pre-commit from a chained hook; husky | Decision 32; scenarios 3 and 5. |

## setup-mstack: installing the skills and rules

Run on 2026-11-20 from the `feat/setup-mstack-skill` worktree, following `skills/setup-mstack/SKILL.md` by hand, as the agent would. `HOME` pointed at an empty temporary folder, so the real `~/.claude/` and `~/.cursor/` were never touched. Answers were given by the agent acting for the user: tools **both**. The temporary `HOME` was seeded with a pstack-style `reflect` skill in `~/.claude/skills/` and an old setup symlink `~/.cursor/skills/sync-rules` pointing into the checkout.

| Step | Result | Evidence |
| --- | --- | --- |
| 1. Tools | Pass | Both: skills go to `~/.claude/skills/` only; rules go to `~/.claude/rules/` and are printed for Cursor Settings. |
| 2. Skills inventory | Pass | `correct-rules`, `reflect-rules`, `sync-rules`: `new`. `sync-rules` is also a `duplicate` (the old symlink in `~/.cursor/skills/`). `setup-mstack` is excluded. Similar: `reflect` ↔ `reflect-rules` (known overlap; both `SKILL.md` files mine the transcript for learnings). |
| 3. Rules inventory | Pass | All five `rules/*.mdc`: `new` as `~/.claude/rules/<name>.md`. |
| 5. Conflicts | Pass | `reflect`: "Add" (both stay installed). Duplicate: "Discard" (the symlink is unlinked, nothing to back up). |
| 6. Apply | Pass | Three skill folders copied (not symlinks), five rules written without frontmatter or `## Checks`, with an `Applies to files matching ...` line. `~/.config/mstack/config.json` has `toolkit_path`. `~/.cursor/skills/` is empty. |
| 8. Verify | Pass | Every skill's `name` matches its folder and has a `description`. `../sync-rules/references/` resolves from every skill. No rule has frontmatter. The config points at a folder with `scripts/`. A second inventory reports `identical`. |
| Skills and rules show up in a new session | Not run | A temporary `HOME` has no login (`claude -p` stops at "Not logged in"), and credentials were not copied. Pending a run on the real `HOME`. |
| Cursor rules pasted into Settings | Not run | Cursor is not available on this machine. |
