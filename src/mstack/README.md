# mstack (package)

The `mstack` command: the guards that `make lint-rules` and the skills run. Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack coverage` | `guards/check_rule_coverage.py` | Every `.mdc` rule has a `## Checks` section, every check it lists exists, and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it. |
| `mstack exceptions` | `guards/check_exceptions.py` | Every `# ast-grep-ignore` names its rules and carries a `# rule-exception:` with a reason, an expiry date that has not passed, and an approver. |
| `mstack leak-check` | `guards/check_no_domain_leak.py` | Rules and checks contain no identifiers from the analyzed repo, and no URLs, emails or secrets. `guards/generic_names.txt` lists names and public hosts it never reports. Known gap: single-word function names (`refund()`, `reconcile()`) are not collected, to avoid false positives on generic verbs. |
| `mstack manifest status --tool claude\|cursor\|both [--json]` | `install/manifest.py` | The state of every skill and rule in the checkout against its installed copy: `new`, `identical`, `upstream-changed`, `locally-edited`, `conflict`, `unknown`, `removed`, `orphan` or `old-symlink`, with the proposed action. |
| `mstack manifest record <kind> <name> <target>` | `install/manifest.py` | After installing an item, record its installed and source hashes, the mstack version and commit. |
| `mstack manifest forget <kind> <name> [--target <path>]` | `install/manifest.py` | Drop an item's record. |
| `mstack render-rule <file.mdc>` | `install/render.py` | Print an `.mdc` rule converted into a Claude Code user rule (no frontmatter, an `Applies to` line from `globs`, no `## Checks`). |

The manifest is machine state, never committed: `${XDG_STATE_HOME:-~/.local/state}/mstack/manifest.json` (`%LOCALAPPDATA%\mstack\manifest.json` on Windows). Hashes are sha256 over the sorted relative paths and contents of a skill's files (ignoring `.DS_Store` and `__pycache__`), or over a rule's rendered text. Writes are atomic, and a manifest with an unknown `schema` fails with a clear message.

Data output (JSON, inventories) goes to stdout; messages go to stderr through `logging`, as `rules/logging.mdc` asks.
