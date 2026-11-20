# Reusable CI action

- **Phase:** now
- **Depends on:** `runtime-lint-command`.

## Problem

`.github/workflows/ci.yml` runs the checks for this repo only. A work repo that adopts rules-as-checks has to copy the steps (checkout with `fetch-depth: 0`, set up uv, full scan, changed-files scan on pull requests), and each copy drifts.

## Goal

Any GitHub repo runs the same checks with one pinned step.

## Out of scope

- Other CI providers. The action is a thin wrapper around `mstack lint`, so any provider can call the CLI directly; document the two commands for them.
- Publishing to the GitHub Marketplace (possible later; the action works by `owner/repo@ref` without it).

## Design

A composite action at the repo root, `action.yml`, so it is used as `uses: justmatias/mstack@v3.1.0`:

```yaml
inputs:
  mode:           # full | changed | both (default: both on pull_request, full otherwise)
  base-ref:       # default: origin/${{ github.base_ref }}
  mstack-version: # default: the action's own ref, so CLI and action always match
  python-version: # default: "3.12"
  working-directory:
```

Steps:

1. Set up uv (`astral-sh/setup-uv`, pinned to a full version, as in `.github/actions/setup-python-env`).
2. `uvx --from "git+https://github.com/justmatias/mstack@${{ github.action_ref }}" mstack lint` for the full scan.
3. On pull requests, the same with `--changed --base-ref <base-ref>`. If the base ref is missing, fail with the message that the caller must check out with `fetch-depth: 0` (the CLI already says so).

The action doesn't check out the code: the caller does, so it controls the depth and the token. It needs only `contents: read`.

**Major tag:** add a step to the `versioning` job that moves a `v<major>` tag to each new release, so callers can choose `@v3` (follows fixes) or a full tag or sha (pinned). The README recommends pinning a full tag or sha.

## Changes

- Add `action.yml`.
- `.github/workflows/ci.yml`: a job `action-self-test` that runs `uses: ./` on this repo, so a broken action fails CI here first.
- `ci.yml` `versioning` job: move the major tag after `semantic-release version` (only when a release was made).

## Tests

- The `action-self-test` job, on both `push` and `pull_request`.
- `actionlint` over the workflows and `action.yml`, as a pre-commit hook or CI step.

## Docs

- `README.md`, "Use the checks in another repo": the workflow snippet, next to the pre-commit one.
- `init-command`'s `--ci github` template uses this action.

## Acceptance criteria

- [ ] A sample workflow in another repo, using only `actions/checkout` with `fetch-depth: 0` and this action, runs the full and changed-files checks.
- [ ] The CLI version always matches the action's ref by default.
- [ ] The action requests no write permissions.
