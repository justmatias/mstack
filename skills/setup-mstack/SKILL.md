---
name: setup-mstack
description: "Install or update the mstack skills (skills/) and rules (rules/) into your user-level Claude Code and Cursor folders, asking you what to add, update, replace or discard for each one. Use when the user says set up mstack, install mstack, update mstack skills, update mstack rules, or after pulling a new version of the mstack repo."
---

# Set up mstack

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including your replies and any combined skill or rule. (2) **Practices, not domain**: a combined skill or rule keeps coding practices only, never business names, rules, values, URLs or verbatim repo code taken from the user's version. Details: [principles.md](../sync-rules/references/principles.md).

Copy the mstack skills and rules from this checkout into the user-level folders that Claude Code and Cursor load. Run it with the mstack repo open: `<mstack>` below is that checkout's root (the folder with `skills/` and `rules/`). Updating is the same flow: pull the repo, then run this skill again.

You do all the work yourself with ordinary file tools (`ls`, `diff -ru`, `cp -R`, `mkdir -p`, `mv`). Nothing is written until the user approves it. Never overwrite or delete anything without a backup.

## 1. Ask which tools the user uses

Ask this first, before reading anything else: **Claude Code, Cursor, or both?** Then state in one or two lines where things will go:

| Tools | Skills go to | Rules go to |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `~/.claude/rules/` |
| Cursor | `~/.cursor/skills/` | Cursor Settings → Rules (pasted by the user, see step 7) |
| Both | `~/.claude/skills/` only, because Cursor also loads that folder and a second copy would show every skill twice | `~/.claude/rules/`, plus Cursor Settings → Rules |

The skills target is called `<skills>` below.

## 2. Inventory the skills

Sources: every folder in `<mstack>/skills/` that has a `SKILL.md`, **except `setup-mstack`** (this skill only runs from the checkout and is never installed). Ignore `.DS_Store` and `__pycache__` when you compare.

For each source skill, look at `<skills>/<name>` and give it one state:

| State | How to tell | Proposed action |
| --- | --- | --- |
| `new` | Nothing there | add |
| `identical` | `diff -ru` shows no difference | none |
| `differs` | `diff -ru` shows differences | ask (step 5) |
| `old-symlink` | A symlink into an mstack checkout (left by the old setup) | replace with a copy |
| `duplicate` | With both tools: a copy or symlink of the same mstack skill in `~/.cursor/skills/` | discard the duplicate |

There is no manifest, so a `differs` skill may be the user's own edit or a newer mstack version: show the diff and let the user decide. Never assume.

Then look for **similar skills**: any other skill in the folders the selected tools load (`~/.claude/skills/`, and `~/.cursor/skills/` with Cursor) that does the same job under another name. Start from [known-overlaps.json](references/known-overlaps.json) (pstack `reflect` ↔ `reflect-rules`, pstack `correct` ↔ `correct-rules`), then compare names and descriptions. For each candidate, read both `SKILL.md` files and keep it only if they really overlap. Say in one line why.

## 3. Inventory the rules (Claude Code)

Skip this step if the user does not use Claude Code.

Sources: every `<mstack>/rules/*.mdc`. Each one installs as `~/.claude/rules/<name>.md`, converted like this:

1. Drop the `.mdc` frontmatter (`description`, `globs`, `alwaysApply`). Claude Code only reads `paths:` from a rule, and `paths:` in user-level rules is unreliable, so the rule is installed without it and always loads.
2. If the rule had `globs`, start the body with one line: `Applies to files matching <globs>.`
3. Drop the `## Checks` section: those checks only run inside the mstack repo.
4. Keep the rest of the body as it is.

Build the converted text, then compare it with what is installed and give each rule a state: `new`, `identical`, or `differs`. Also look for **similar rules** in `~/.claude/rules/` (same topic under another file name) by reading them, and keep only real overlaps.

## 4. Show the plan and wait

Show one table, one row per skill or rule: name, kind (skill or rule), purpose (one line, in your own words, from its `description` and body: what it does and when it is used), state, proposed action, and "similar to `<name>`" for confirmed overlaps. Wait for the user's approval. Do not ask about rows whose action is obvious (`new` → add, `identical` → nothing, `old-symlink` → replace with a copy).

## 5. Ask about every conflict

For each `differs` item, each confirmed similar item, and anything the user wants to change in the table, ask the user to pick one option. "Theirs" is mstack's version, "mine" is the installed one:

| Choice | Effect |
| --- | --- |
| **Add** | Install mstack's version. For a similar item with a different name, both stay installed. |
| **Update** | Back up the installed version, then install mstack's version over it. |
| **Replace** | For a similar item: back up the user's item and remove it, then install mstack's version. |
| **Discard** | Do not install mstack's version, and leave what is installed untouched. For a `duplicate`, back it up and remove it. |
| **Combine** | Draft one merged item (see below) and install it after approval. |

Ask about one item at a time, and give the user what they need to decide without opening any file:

1. **Purpose.** In two or three lines, say what the mstack version does and when it is used. For a `differs` item, also say what the installed version does. For a similar item, say what the user's skill or rule does and where the two overlap or differ in purpose.
2. **What changed.** Summarize the differences in plain words (for example "adds a `--check` mode", "drops the reviewer templates", "only the wording of step 3 changed"), and say whether they look like the user's own edits or a newer mstack version.
3. **The diff** (`diff -ru` for a skill, `diff -u` for a rule). For a long diff, show the parts that matter and offer the rest.
4. **Your recommendation** and one line of why, then the question.

**Combine:**

1. Draft the merged item in a temp folder outside the repo and outside every tool folder. Start from mstack's version and bring over what only the user's version has.
2. A merged skill keeps the frontmatter `name` equal to its folder name. If either side had the principles header (`> **Principles (always apply):** ...`), the merged skill keeps it at the top. If either side credits pstack (`license` and `metadata.adapted-from` in the frontmatter, or an `Adapted from pstack/<skill> (MIT)` line), the merged skill keeps that credit in its frontmatter.
3. Relative links into `../sync-rules/references/` must still resolve: every mstack skill is installed side by side in `<skills>`.
4. Show the diff of the draft against both versions, and install it only after the user explicitly approves it.

## 6. Apply what was approved

- **Back up first.** Move whatever you are about to overwrite or remove into `<folder>/.mstack-backups/<UTC timestamp>/<name>`, inside the folder it came from (for example `~/.claude/skills/.mstack-backups/20261120-101500/sync-rules/`). Never put backups next to the skills or rules as `<name>.bak` or similar: the tools would load them.
- A symlink is removed with `rm` (its target is the checkout; nothing to back up).
- Copy skills with `cp -R <mstack>/skills/<name> <skills>/<name>`, then delete any `.DS_Store` or `__pycache__` that came along.
- Write each converted rule to `~/.claude/rules/<name>.md`.
- Install the `mstack` CLI, which the installed skills call to run the guards (see `../sync-rules/references/authoring-a-check.md`). If `mstack --help` already works, leave it. Otherwise ask the user, then run `uv tool install --editable <mstack>`.

## 7. Cursor rules

Skip this step if the user does not use Cursor. Cursor has no file-based user rules folder (it does not load `~/.cursor/rules/`), and its user rules live in Cursor Settings → Rules. So:

1. Ask the user which mstack rules they want in Cursor (default: the ones they approved for Claude Code, or all of them).
2. Print them as one block of plain text, ready to paste: for each rule, its `description` as a heading, the `Applies to ...` line, and the body without frontmatter or `## Checks`.
3. Tell the user to paste it into **Cursor Settings → Rules → User Rules**. Do not edit Cursor's settings database.

## 8. Verify

- `mstack skills-check <skills> --profile generic` passes: every installed skill has a `SKILL.md` whose frontmatter `name` matches its folder and has a `description`, and every relative link resolves, `../sync-rules/references/` included. Fix every error it reports; mention its warnings to the user.
- No mstack skill exists in both `~/.claude/skills/` and `~/.cursor/skills/` when the user picked both.
- Every installed rule exists in `~/.claude/rules/` and has no frontmatter.
- `mstack --help` runs.

Tell the user the skills and rules show up in a new session of Claude Code or Cursor.

## 9. Reply

A short list. Leave out empty lines:

- Skills added / updated / replaced / combined / discarded: ...
- Rules added / updated / replaced / combined / discarded: ...
- Duplicates removed and old symlinks replaced: ...
- Cursor rules: printed for pasting (or skipped).
- Backups: `<folder>/.mstack-backups/<timestamp>/`
