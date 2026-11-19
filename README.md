# rules-as-checks

Team rules are written in prose in `.cursor/rules/`. This repo turns every rule that can be verified into an automated check (ast-grep and import-linter), runs the checks in the agent hook, in pre-commit and in CI, and ships three skills that keep prose and checks in sync.

The reasoning and the decisions behind it are in [`docs/design.md`](docs/design.md). Decisions taken during implementation are in [`docs/decisions.md`](docs/decisions.md).

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
make setup        # uv sync, pre-commit install, install the skills
make lint-rules   # the single command: tests, scan, contracts and guards
make demo         # scans demo/violations/ and expects it to fail
```
