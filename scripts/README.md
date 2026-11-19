# scripts

Repo-level tooling behind the `make` targets: picking the changed files, running the checks from agent hooks, and installing the integrations. Nothing is meant to be called directly: each one runs through the `make` target listed below.

The guards and generators (rule coverage, exceptions, domain leaks, conventions inventory, rules table) are not here: they are the `mstack` package in `src/mstack/`, run as `mstack <command>` (`mstack --help`), so the skills can call them from any repo. `make guards` and `make rules-table` run them with `uv run mstack`.

| Folder | What it holds | Run by |
| --- | --- | --- |
| `git/` | Helpers that read the git state. | `make lint-rules-changed` |
| `hooks/` | Agent hooks that scan each edited file and report findings back to the agent. | Claude Code / Cursor, once installed by `make setup` |

## git/

- `changed_files.sh`: lists the `.py` files changed relative to `origin/main` (`BASE_REF` overrides it), or the staged files with `--staged`.

## hooks/

- `claude_post_edit.sh`: Claude Code `PostToolUse` hook; on rule errors in the edited `.py` file, prints them to stderr and exits 2.
- `cursor_after_edit.sh`: Cursor `postToolUse` hook (no matcher); acts on any tool whose input names a `.py` file and returns the findings as `additional_context`.
- `lib.sh`: helpers shared by both hooks (read the edited path from the payload, scan one file, log calls when `MSTACK_HOOK_DEBUG=1`).

## setup.py

- `setup.py`: the configurable setup CLI behind `make setup`. Installs or removes pre-commit, the agent hooks and the skills (`--help` lists the flags).
