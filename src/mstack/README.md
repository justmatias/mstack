# mstack (package)

The `mstack` command: the guards that `make lint-rules` and the skills run. Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack config` | `config.py` | Prints the resolved project config and where each value comes from (`default`, `file` or `flag`). `--json` prints it as JSON. |
| `mstack coverage` | `guards/check_rule_coverage.py` | Every `.mdc` rule has a `## Checks` section, every check it lists exists, and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it. |
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

[scan]
exclude = []                         # globs the scan skips; mstack exceptions skips them too
extensions = [".py"]                 # what a changed-files scan considers

[leak_check]
paths = ["lint-rules", ".cursor/rules"] # what mstack leak-check checks when given no paths
exclude = []                         # tooling folders that are not analyzed code

[changed]
base_ref = "origin/main"
```

`mstack leak-check --repo` defaults to the git root. Run `mstack config` to see the resolved values; this repo's own `.mstack.toml` is an example.
