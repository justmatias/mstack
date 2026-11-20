# mstack (package)

The `mstack` command: the guards that `make lint-rules` and the skills run. Install it on your `PATH` with `uv tool install --editable <checkout>`; inside this repo, `uv run mstack` uses the dev environment.

| Command | Module | What it does |
| --- | --- | --- |
| `mstack coverage` | `guards/check_rule_coverage.py` | Every `.mdc` rule has a `## Checks` section, every check it lists exists, and every ast-grep rule or import-linter contract points back to an `.mdc` that lists it. |
| `mstack exceptions` | `guards/check_exceptions.py` | Every `# ast-grep-ignore` names its rules and carries a `# rule-exception:` with a reason, an expiry date that has not passed, and an approver. |
| `mstack leak-check` | `guards/check_no_domain_leak.py` | Rules and checks contain no identifiers from the analyzed repo, and no URLs, emails or secrets. `guards/generic_names.txt` lists names and public hosts it never reports. Known gap: single-word function names (`refund()`, `reconcile()`) are not collected, to avoid false positives on generic verbs. |
| `mstack skills-check` | `guards/check_skills.py` | Every skill (a folder with a `SKILL.md`, default `skills/`) passes the checks below. Errors fail the command; warnings only print. |

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
