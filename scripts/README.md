# scripts

Repo-level tooling behind the `make` targets: picking the changed files. Nothing is meant to be called directly: each one runs through the `make` target listed below.

The guards (rule coverage, exceptions, domain leaks) are not here: they are the `mstack` package in `src/mstack/`, run as `mstack <command>` (`mstack --help`), so the skills can call them from any repo. `make guards` runs them with `uv run mstack`.

| Folder | What it holds | Run by |
| --- | --- | --- |
| `git/` | Helpers that read the git state. | `make lint-rules-changed` |

## git/

- `changed_files.sh`: lists the `.py` files changed relative to `origin/main` (`BASE_REF` overrides it), or the staged files with `--staged`.
