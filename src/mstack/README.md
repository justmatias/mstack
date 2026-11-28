# mstack (package)

The `mstack` command installs and checks mstack's content on this machine: `cleanup`, `doctor`, `platform`, `render-rule`, `rule-tests-check` and `skills-check`, and the `coverage` guard. The ast-grep and import-linter checks run through [rulepack](https://github.com/justmatias/rulepack). Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack doctor [--tool TOOLS] [--checkout DIR] [--online] [--json]` | `doctor/` | Checks that this machine is set up (see below). |
| `mstack cleanup [--apply] [--checkout DIR]` | `cleanup.py` | Previews old backup batches and their sizes. `--apply` deletes eligible batches. |
| `mstack platform [--json]` | `platform.py` | Prints the detected platform (`linux`, `macos`, `windows` or `wsl`) and each tool's user folder. On WSL, Cursor's is the Windows profile's `.cursor`, found with `cmd.exe` and `wslpath`; `MSTACK_WINDOWS_HOME` overrides it and `MSTACK_PLATFORM` overrides the detection. `mstack doctor` uses the same folders, so on WSL with both tools skills and agents get a copy in each home. |
| `mstack render-rule <file.mdc>` | `render.py` | Print an `.mdc` rule converted into a Claude Code user rule (no frontmatter, an `Applies to` line from `globs`, no `## Checks`, and the upstream credit, if any, as its last lines). |
| `mstack render-rule --combined <checkout>` | `render.py` | Print the managed Codex instructions block with the rendered rules. |
| `mstack rule-tests-check [--sgconfig FILE] [--json]` | `guards/check_rule_tests.py` | Every ast-grep rule under the sgconfig's `ruleDirs` (default `lint/sgconfig.yml`, nested folders included) has a rule test under `testConfigs` with at least one `valid` and one `invalid` case, every rule test names a rule, and no rule id repeats. Exits 2 when the sgconfig or a rule file cannot be read. |
| `mstack skills-check` | `guards/check_skills.py` | Every skill (a folder with a `SKILL.md`, default `skills/`, which may group skills in topic folders) passes the checks below. Errors fail the command; warnings only print. |
| `mstack coverage [--rules-dir DIR] [--config FILE] [--importlinter FILE] [--pre-commit-config FILE] [--root DIR] [--json]` | `guards/coverage.py` | Every prose rule has a `## Checks` section whose `enforced-by:` ids exist as ast-grep rules or import-linter contracts and whose `enforced-by-hook:` ids are configured pre-commit hooks, every `metadata.source` link is valid, and rule credit is complete. |

`mstack coverage` reads `sgconfig` and `importlinter` from the nearest `.rulepack.toml`, from the current folder up to the git root. The rules folder (`.cursor/rules`) and the pre-commit config (`.pre-commit-config.yaml`) default to that file's folder; the flags override them. A config error exits 2.

`mstack skills-check [DIR ...] [--profile mstack|generic] [--json]` takes folders of skills, or a single skill folder. Relative links resolve as if the skills were installed side by side, so a link to a sibling skill (`../<name>/...`) works whichever group the checkout keeps it in, and a link out of the skills folder fails.

| Check | Profile | Reports when |
| --- | --- | --- |
| `frontmatter` | both | the `---` block is missing, is not YAML, or is not a mapping |
| `name` | both | `name` is missing, not kebab-case, or not the folder name |
| `description` | both | `description` is missing, empty, or longer than 1024 characters |
| `keys` | both | a frontmatter key is unknown. An error under `mstack`, which allows `name`, `description`, `license`, `metadata` and `disable-model-invocation`; a warning under `generic`, which also allows the optional Claude Code and Cursor keys |
| `links` | both | a relative Markdown link outside code points to a missing file, or out of the skills folder |
| `unused-files` | both | a file under `references/` or `scripts/` is neither linked nor named by its path (warning) |
| `principles` | mstack | the first block after the title is not the `> **Principles (always apply):**` header |
| `credit` | mstack | `license` without `metadata.adapted-from`, or the reverse; an `adapted-from[-<label>]` without an `upstream-commit[-<label>]` that is a 40-character sha |
| `english` | mstack | a non-ASCII letter outside code and double-quoted examples (warning) |

Use `--profile generic` for skills that aren't mstack's, such as a user's `~/.claude/skills/`.

### `mstack cleanup`

Running `mstack cleanup` lists timestamped batches under known user and uv tool
`.mstack-backups` directories, with their sizes in bytes. It keeps the newest
batch in each directory and only lists other batches older than 30 days.
Run `mstack cleanup --apply` to recalculate the list and delete those batches.
Add `--checkout DIR` to include that checkout's `rules/` folder and
its parent, `skills/`, and the immediate skill groups.

### `mstack doctor`

Reports the fix for each problem. `--tool` takes a comma-separated list of `claude`, `cursor` and `codex`, with `both` as an alias for Claude Code and Cursor. By default, doctor checks the tools whose folders exist (`~/.claude`, `~/.cursor` and `~/.codex` or `CODEX_HOME`). The checkout defaults to the one the CLI was installed from. Any error gives exit code 1. With `--json`, the report goes to stdout and the table goes to stderr.

| Group | Checks | Status when it fails |
| --- | --- | --- |
| `tools` | `uv` and `git` on `PATH`; `gh` (used by `correct` and `integrate`) | error; warn for `gh` |
| `cli` | `mstack` on `PATH` reports this version (`mstack --version`); `rulepack` is on `PATH` and runs. The fix installs the tag in `[tool.mstack] rulepack` | error |
| `source` | the checkout exists and is a git repo; uncommitted changes | error; warn |
| `skills` | expected folders contain every mstack skill and pass `skills-check --profile generic`. Codex uses `~/.agents/skills/`. Cursor warns when a skill appears in multiple user skill folders it loads | error; warn for duplicates |
| `rules` | Claude Code rules exist without frontmatter. The active Codex global instructions file has exactly one managed block | error |
| `drift` | skills, Claude Code and Cursor agents, and rendered Claude Code and Codex rules match the checkout. For Codex, only the text inside the managed block is compared | warn; error when the checkout's rules fail to render |
| `platform` | on WSL with Cursor: the Windows profile was found (from `mstack.platform`), so Cursor's files are checked there | warn |
| `version` | with `--online` only: the latest `v*` tag on the checkout's `origin` (`git ls-remote`) is not newer | warn |

Each check is a function from a `Context` to a list of results, registered in `doctor/__init__.py`'s `CHECKS`. Without `--online`, doctor uses no network.

Data output (JSON, inventories) goes to stdout; messages go to stderr through `logging`.
