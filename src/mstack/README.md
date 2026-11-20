# mstack (package)

The `mstack` command: `mstack lint` and the guards that `make lint-rules` and the skills run. ast-grep and import-linter are runtime dependencies, so the installed CLI brings its own. Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack config` | `config.py` | Prints the resolved project config and where each value comes from (`default`, `file` or `flag`). `--json` prints it as JSON. |
| `mstack lint` | `lint.py`, `changed_files.py` | Runs every check in order (see below). |
| `mstack commit-msg <file>` | `guards/check_commit_msg.py` | The commit message in the file (as a `commit-msg` hook passes it) has a Conventional Commits subject `type(scope)!: summary` with a type from `[commits].types`, at most 72 characters and no trailing period, and a blank line before the body. Comment lines and everything below git's scissors line are ignored; `Merge ...`, `Revert "..."`, `fixup!`, `squash!` and `amend!` messages pass. Each error names the rule it breaks and prints a corrected example. |
| `mstack init` | `init.py`, `templates/` | Scaffolds the rules-as-checks layout in a repo (see below). |
| `mstack doctor [--tool claude\|cursor\|both] [--checkout DIR] [--online] [--json]` | `doctor/` | Checks that this machine is set up (see below). |
| `mstack platform [--json]` | `platform.py` | Prints the detected platform (`linux`, `macos`, `windows` or `wsl`) and each tool's user folder. On WSL, Cursor's is the Windows profile's `.cursor`, found with `cmd.exe` and `wslpath`; `MSTACK_WINDOWS_HOME` overrides it and `MSTACK_PLATFORM` overrides the detection. `mstack manifest status` and `mstack doctor` use the same folders, so on WSL with both tools skills and agents get a copy in each home. |
| `mstack coverage` | `guards/check_rule_coverage.py` | Every `.mdc` rule has a `## Checks` section, every check it lists exists (`enforced-by:` an ast-grep rule or import-linter contract; `enforced-by-hook:` a hook id in `.pre-commit-config.yaml`, else `unknown-hook`), and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it. `--json` lists each rule's `checks` and `hooks`. |
| `mstack exceptions` | `guards/check_exceptions.py` | Every `# ast-grep-ignore` names its rules and carries a `# rule-exception:` with a reason, an expiry date that has not passed, and an approver. |
| `mstack leak-check` | `guards/check_no_domain_leak.py` | Rules and checks contain no identifiers from the analyzed repo, and no URLs, emails or secrets. `guards/generic_names.txt` lists names and public hosts it never reports. Known gap: single-word function names (`refund()`, `reconcile()`) are not collected, to avoid false positives on generic verbs. |
| `mstack config-check [--root <dir>]` | `guards/check_agent_config.py` | `agents/*.md` have a frontmatter `name` equal to the file name and a `description`; `mcp/*.json` and `settings/*.json` are JSON objects (an MCP entry has a `command` or a `url`); no literal secrets (sensitive keys must hold a `${VAR}` placeholder) and no machine-specific paths. |
| `mstack manifest status --tool claude\|cursor\|both [--json]` | `install/manifest.py` | The state of every skill, rule, agent, MCP server, settings fragment and global instructions in the checkout against its installed copy: `new`, `identical`, `upstream-changed`, `locally-edited`, `conflict`, `unknown`, `removed`, `orphan` or `old-symlink`, with the proposed action. |
| `mstack manifest record <kind> <name> <target>` | `install/manifest.py` | After installing an item, record its installed and source hashes, the mstack version and commit. |
| `mstack manifest forget <kind> <name> [--target <path>]` | `install/manifest.py` | Drop an item's record. |
| `mstack merge-settings <fragment> <target> [--under <key>]... --dry-run\|--write` | `install/merge.py` | Deep-merge a JSON fragment into a JSON file: objects by key, arrays as unions, mstack's scalars win, keys it does not define untouched. Prints every change as JSON; a dry run writes nothing. |
| `mstack merge-block <file> <target> --dry-run\|--write` | `install/merge.py` | Put a file's text in the `<!-- mstack:begin -->` … `<!-- mstack:end -->` block of the target, appending the block when missing. Text outside the markers is kept. |
| `mstack render-rule <file.mdc>` | `install/render.py` | Print an `.mdc` rule converted into a Claude Code user rule (no frontmatter, an `Applies to` line from `globs`, no `## Checks`). |
| `mstack skills-check` | `guards/check_skills.py` | Every skill (a folder with a `SKILL.md`, default `skills/`) passes the checks below. Errors fail the command; warnings only print. |

The manifest is machine state, never committed: `${XDG_STATE_HOME:-~/.local/state}/mstack/manifest.json` (`%LOCALAPPDATA%\mstack\manifest.json` on Windows). Hashes are sha256 over the sorted relative paths and contents of a skill's files (ignoring `.DS_Store` and `__pycache__`), a rule's rendered text or an agent file. For merged items, the installed hash covers only what mstack owns: the managed block, or the part of the JSON file that the fragment defines, so the user's own keys and text never change the state. Their records also list the JSON keys mstack wrote (`keys`). Writes are atomic, and a manifest with an unknown `schema` fails with a clear message.

`mstack skills-check [DIR ...] [--profile mstack|generic] [--json]` takes folders of skills, or a single skill folder. Relative links resolve as if the skills were installed side by side, so a link to a sibling skill works and a link out of the skills folder fails.

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

### `mstack lint`

```text
mstack lint [--changed [--base-ref REF] [--staged]] [--files FILE ...]
            [--only STEP ...] [--skip STEP ...] [--json]
```

| Step | Runs | Skipped when |
| --- | --- | --- |
| `test` | `ast-grep test -c <sgconfig> --skip-snapshot-tests` | the sgconfig's `testConfigs` hold no test files |
| `scan` | `ast-grep scan -c <sgconfig>`, skipping the `[scan].exclude` globs | `--changed` or `--files` selected no file |
| `imports` | `lint-imports` | there is no `.importlinter` (the configured `importlinter`) |
| `coverage` | `mstack coverage` | there is no rules folder |
| `exceptions` | `mstack exceptions` | never |
| `leak-check` | `mstack leak-check` over `[leak_check].paths` | none of the paths exist |

- **Modes.** By default the scan covers the whole repo and warnings don't fail. `--changed` scans only the files changed against `[changed].base_ref` (`--base-ref` overrides it, `--staged` uses the staged files), and passes `--error`, so warnings fail on new or touched code. `--files` scans exactly the given files with `--error` (for pre-commit). Both keep only files with a `[scan].extensions` suffix that are not excluded.
- **Changed files.** Committed changes since the merge base, uncommitted changes and untracked files; deleted files are left out. An explicit `--base-ref` that doesn't exist fails (in CI, check out with `fetch-depth: 0`); the configured default falls back to its local branch (`origin/main` to `main`).
- **All steps run**, even after a failure, and the exit code is 1 if any failed (2 for a usage or git error). `--json` prints `{step: {ok, skipped, findings}}` to stdout: scan findings carry `file`, `line`, `rule`, `severity` and `message`; the other steps list their error messages.
- **Tools.** ast-grep and lint-imports are taken from the environment mstack runs in (next to its Python) before `PATH`, so the bundled versions win. For `imports`, a repo whose `uv.lock` lists import-linter runs its own (`uv run --frozen lint-imports`), because the contracts need the project importable; otherwise the bundled one runs with the repo root and `src/` on `PYTHONPATH`. The log says which one ran.
- The guards run in process, through their `main()` functions.

### `mstack init`

```text
mstack init [--rules-dir DIR] [--checks-dir DIR]
            [--pre-commit] [--ci github] [--makefile] [--dry-run] [--yes]
```

- Always: `.mstack.toml` with the chosen folders (defaults `.cursor/rules` and `lint-rules`), `<checks-dir>/sgconfig.yml`, empty `rules/` and `rule-tests/` (with a `.gitkeep`), and `<rules-dir>/` when missing.
- `--pre-commit`: adds the mstack hooks to `.pre-commit-config.yaml`, pinned to the running version's tag, at the end of `repos:` (the rest of the file is untouched). Creates the file when missing.
- `--ci github`: `.github/workflows/mstack.yml`, which runs the mstack action at the running version's tag.
- `--makefile`: the `lint-rules` and `lint-rules-changed` targets, each only when the Makefile doesn't define it yet.

It prints every file as `create`, `append` or `exists, skipped` and asks before writing, unless `--yes`; `--dry-run` only prints. It never overwrites a file and appends only missing entries, so a second run changes nothing. If the repo already has a `.mstack.toml` (or `[tool.mstack]`) or a `lint-rules/sgconfig.yml`, the layout is left as it is and only missing optional pieces are added. After writing it runs `mstack lint` once; an empty layout passes. The templates are in `templates/` and ship in the wheel.

### `mstack doctor`

Reports only, and prints the fix for each problem. `--tool` defaults to the tools whose folders exist (`~/.claude`, `~/.cursor`); the checkout defaults to the one the CLI was installed from. Exit 1 on any `error`; `--json` prints the report to stdout, and the table goes to stderr.

| Group | Checks | Status when it fails |
| --- | --- | --- |
| `tools` | `uv` and `git` on `PATH`; `gh` (used by `correct-rules` and `integrate-skills`) | error; warn for `gh` |
| `cli` | `mstack` on `PATH` reports this version (`mstack --version`); the bundled ast-grep runs | error |
| `source` | the checkout exists and is a git repo; uncommitted changes | error; warn |
| `skills` | every mstack skill is in the tool's skills folder; every skill there passes `skills-check --profile generic`; none is in both `~/.claude/skills/` and `~/.cursor/skills/` | error; warn for duplicates |
| `rules` | every mstack rule is in `~/.claude/rules/` without frontmatter (Claude Code only) | error |
| `drift` | when the manifest exists: every `mstack manifest status` state other than `identical` | warn |
| `platform` | on WSL with Cursor: the Windows profile was found (from `mstack.platform`), so Cursor's files are checked there | warn |
| `version` | with `--online` only: the latest `v*` tag on the checkout's `origin` (`git ls-remote`) is not newer | warn |

Each check is a function from a `Context` to a list of results, registered in `doctor/__init__.py`'s `CHECKS`. Without `--online`, doctor uses no network.

Data output (JSON, inventories) goes to stdout; messages go to stderr through `logging`, as `rules/logging.mdc` asks.

## Configuration

Every command reads one optional file that describes the repo's layout, so no command needs path flags:

- `.mstack.toml`, found by walking up from the current directory to the git root (never above it). Python repos may instead use a `[tool.mstack]` table in `pyproject.toml`; if both exist, `.mstack.toml` wins and a warning is logged.
- Precedence: a command-line flag, then the file, then the built-in defaults below. A repo without the file gets the defaults.
- Paths in the file are relative to the file's folder; paths in flags are relative to the current directory.
- Unknown keys are an error, so a typo fails loudly instead of being ignored.

```toml
rules_dir = ".cursor/rules"          # prose rules (*.mdc)
sgconfig = "lint-rules/sgconfig.yml" # ast-grep config
importlinter = ".importlinter"       # optional; skipped when missing
pre_commit_config = ".pre-commit-config.yaml" # hook ids that enforced-by-hook may name

[scan]
exclude = []                         # globs the scan skips; mstack exceptions skips them too
extensions = [".py"]                 # what mstack lint --changed and --files scan

[leak_check]
paths = ["lint-rules", ".cursor/rules"] # what mstack leak-check checks when given no paths
exclude = []                         # tooling folders that are not analyzed code

[changed]
base_ref = "origin/main"

[commits]
types = ["build", "chore", "ci", "docs", "feat", "fix", "perf", "refactor", "style", "test"]
```

`mstack leak-check --repo` defaults to the git root. Run `mstack config` to see the resolved values; this repo's own `.mstack.toml` is an example.
