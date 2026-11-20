# Version pinning across machines

- **Phase:** future
- **Depends on:** `packaged-install` (install a given tag), `install-manifest` (the installed version). Better with `host-profiles` (pin per profile).

## Problem

Each machine ends up on whatever was last pulled. With no way to see or pin the installed version, the personal and work laptops drift, and an update can bring changes nobody reviewed.

## Goal

Know which version each machine runs, move to a chosen version on purpose, and see what changed before updating.

## Design

```text
mstack version              # CLI version, installed assets version, source (checkout or tag)
mstack update --to v3.2.0   # install exactly that release
mstack changes [FROM] [TO]  # CHANGELOG.md sections between two versions (default: installed → latest)
```

- **Pin:** `~/.config/mstack/config.toml` key `version = "3.2.0"` (shared with `host-profiles`). `mstack update` without `--to` goes to the pinned version, or the latest when there's no pin. `doctor` warns when the installed version differs from the pin.
- **Changes:** parse the semantic-release `CHANGELOG.md` (already generated on every release) and print the sections between two versions, highlighting breaking changes (`!`, `BREAKING CHANGE`). `update` shows them before confirming.
- **Same version everywhere:** keeping the pin in a dotfiles repo, or in the profile (`host-profiles`), is what keeps both laptops on the same version.

## Changes

- `src/mstack/version.py` (version info and changelog parsing), plus `update --to` in the install command.
- `doctor`: the pin check.

## Tests

- Changelog parsing on the real `CHANGELOG.md`: a range, breaking-change detection, unknown versions.
- `update --to` in a temporary environment (install, then another tag).

## Acceptance criteria

- [ ] `mstack version` on two machines tells whether they match.
- [ ] `mstack update` shows the changes and asks before moving to a new version.
