# Install without a checkout

- **Phase:** future
- **Depends on:** `install-command`.

## Problem

The CLI must be an editable install of a local clone (`uv tool install --editable .`), because the skills, rules and other folders are read from the checkout. On a work laptop where the user only wants to *use* the stack, cloning and keeping a checkout up to date is extra friction.

## Goal

`uv tool install git+https://github.com/justmatias/mstack@vX.Y.Z` followed by `mstack install` is enough. The checkout stays the way to *develop* mstack.

## Out of scope

- Publishing to PyPI (possible later with the same wheel).

## Design

- **Package data:** the wheel includes `skills/`, `rules/`, `lint/`, `agents/`, `mcp/`, `instructions/`, `settings/`, `hooks/` and `packs.toml`. Check whether the `uv_build` backend can include top-level folders in the package. If it can't, move them under `src/mstack/assets/` and leave nothing at the top level, rather than keeping two copies.
- **One resolver:** `src/mstack/assets.py` returns the root of these folders. For an editable install it is the checkout, and for a regular install it is `importlib.resources.files("mstack") / "assets"`. Every command (install, doctor, packs) uses it, and none reads paths relative to the repo.
- **Source identity:** the manifest records the package version, and the commit when it is known (from the editable checkout, or written into the wheel at build time).
- **Update:** with a packaged install, `mstack update` runs `uv tool upgrade mstack` (or reinstalls at a given tag), then `mstack install`.

## Changes

- `pyproject.toml` build configuration, `src/mstack/assets.py`, and switching every reader to it.
- `doctor`'s `source` check handles both modes.
- `README.md`, "Getting started": two paths, "use it" (packaged) and "work on it" (checkout).

## Tests

- Build the wheel in CI, install it into a temporary environment, and run `mstack install --dry-run --json` in a temporary `HOME`. The plan lists every skill and rule.
- A test that the wheel contains every file under the asset folders that git tracks.

## Acceptance criteria

- [ ] A machine with no checkout installs and updates the stack from a git tag.
- [ ] The editable install keeps working for development.
