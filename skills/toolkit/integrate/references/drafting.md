# Drafting an integrated skill or rule

> **Principles (always apply):** (1) **English only**: everything you write is in English, even when the upstream is not. (2) **Practices, not domain**: keep coding practices only, never the upstream project's business names, values, URLs or verbatim code. Details: [../../sync/references/principles.md](../../sync/references/principles.md).

Draft in `<tmp>/draft/`, never in the target.

## Credit (every route)

```yaml
license: <SPDX id of the upstream license>
metadata:
  adapted-from: "<path> in <owner>/<repo> (https://github.com/<owner>/<repo>/tree/<sha>/<path>). Thanks to <author> for the original."
  upstream-commit: "<40-character sha>"
  upstream-license: "<SPDX id>, <copyright line>, https://github.com/<owner>/<repo>/blob/<sha>/LICENSE"
```

For something written from the idea only (no license), use `metadata.inspired-by` with the URL, and no `license` or `upstream-license`. When the target already credits another upstream, add this one under suffixed keys (`adapted-from-<label>`, `upstream-commit-<label>`, `upstream-license-<label>`).

## Skills (`<tmp>/draft/<name>/`)

1. **Name:** kebab-case folder equal to the frontmatter `name`. Keep the upstream name unless it collides or the user picks another.
2. **Description:** English, what the skill does plus the phrases that trigger it (`Use when ...`), under 1024 characters.
3. **Invocation:** `disable-model-invocation: true` when it should only run by name (writes files, spawns subagents, reaches the network).
4. **Principles header:** right after the title, the `> **Principles (always apply):** ...` line every mstack skill carries, adapted to what this skill writes, linking to `principles.md`. Every other `.md` in the skill states both principles in its first lines.
5. **Body:** translate to English, replace domain names, URLs and values with generic ones (`Foo`, `Item`, `do_work`) or drop them. Do not copy the upstream README, changelog or marketing text.
6. **Links and tools:** every relative link resolves inside the skill or to a sibling skill installed with it. Where the upstream names tools for one agent, say what to use in Claude Code and in Cursor (see `../../sync/references/discovery.md`).
7. **Files:** keep only what the `SKILL.md` uses. No `.DS_Store`, `__pycache__`, lockfiles or upstream CI.

## Rules (`<tmp>/draft/rules/<name>.mdc`, format in [rule-format.md](../../sync/references/rule-format.md))

1. **One `.mdc` per topic**, named for it (`fixtures.mdc`, not `upstream-rules.mdc`), with a `description`, structural `globs` and `alwaysApply: false` unless it applies to every request.
2. **Atomic bullets in your own words:** one verifiable statement each, with a `Why:` line. Never paste upstream wording, examples or code.
3. **Checks:** use [sync](../../sync/SKILL.md) to select enforcement. Use an existing linter when it covers the standard. For a new check, add cases and prove it fails on a synthetic mistake. An upstream check may seed it, rewritten under the target's ids and `metadata.source`. Draft checks in `<tmp>/draft/lint/...`; run `sync` on the target only after approval.
4. No principles header in rules.

## Merge

Start from the target, not the upstream: its name, structure, voice and principles stay. Bring over only what it lacks (a step, mode, check, reference or bullet), in the target's style, and say where each piece came from. For a rule, extend its `Why:` only if the upstream gave a reason the target lacks. For a **conflicts** row, write only the side the user picked.

## Rebase

1. Read the old sha from `metadata.upstream-commit` (or the suffixed key) and fetch it: `git -C <tmp>/upstream fetch origin <old-sha>`.
2. Diff only the upstream changes: `git -C <tmp>/upstream diff --find-renames <old-sha> <sha> -- <path>`.
3. Apply each change in the target's words and keep every local adaptation it does not touch. If a change conflicts with one, ask which wins. A rule the upstream removed is not removed here without asking.
4. Update the sha, and `upstream-license` if the license changed (back to the license check if it is no longer permissive).
