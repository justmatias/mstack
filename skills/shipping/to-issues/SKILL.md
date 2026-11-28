---
name: to-issues
description: "Move planned work kept as Markdown specs in a repo (docs/specs/, specs/, plans/, rfcs/ or a path you name) into GitHub issues, one issue per spec: the spec's title becomes the issue title, its text becomes the body with a permalink to the source, dependencies between specs become issue references, existing issues are reused instead of duplicated, and each issue is verified after it is created. Then removes the spec files and points their links at the issues. Also splits an issue that bundles several specs into one issue per spec. Use for /to-issues, move the specs to issues, turn these plans into issues, migrate docs/specs to GitHub, or split this issue into one per spec."
disable-model-invocation: true
---

# To issues

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the issue titles, bodies and comments, even when the spec is not. (2) **Practices, not domain**: an issue carries the spec's own text and the links a reader needs; it never adds business details, values or URLs the spec did not already contain. Details: [../sync/references/principles.md](../sync/references/principles.md).

Turn each spec into one GitHub issue, so planned work lives where it is tracked and the repo only describes what exists. One spec, one issue: never merge several specs into one issue, and never split one spec across several.

## 1. Find the specs

- **A folder** (`docs/specs/`, `specs/`, `plans/`, `rfcs/`, or the path the user names): each Markdown file is one spec. An index (`README.md`, `index.md`) is not a spec. Read it for what it adds: phases, dependencies, the shared goal.
- **One file with several specs**: only when the user says so, one spec per top-level section.
- **An issue that bundles several specs**: one spec per section or `<details>` block. When it links the original files at a commit, use those files (`git show <sha>:<path>`) as the source. They are the unedited text.

Read every spec in full. For each, note its title (the first `# ` heading, else the file name), a one-line summary, which other specs it depends on, and whether it already shipped: search the repo for what it says it adds. List a shipped spec as "delete, no issue" in the plan instead of opening an issue for finished work.

## 2. Check what exists

- `gh issue list --state all --search "<title> in:title" --json number,title,state,url` for each spec. An open issue for the same spec is reused, not duplicated. Show its number in the plan, and update its body only if the user approves.
- `gh label list` for the labels that exist. Use only those (for example `enhancement` for planned features), and never create labels.

## 3. Show the plan

One table: spec, issue title, labels, depends on, and what happens (create, reuse, delete with no issue). Then one line on the files to delete and the links to repoint. Wait for approval, unless the request already named these specs and asked for the issues.

## 4. Create the issues

Create them in dependency order, so a spec can reference the issue it depends on by number.

Write each body to a temporary file outside the repo and pass it with `--body-file`, so the shell never rewrites the Markdown:

1. A first line: `Moved from [<path>](<permalink>).` The permalink is pinned at a commit SHA (`https://github.com/<owner>/<repo>/blob/<sha>/<path>`), so it still resolves after the file is deleted.
2. The spec's text, unchanged, minus its `# ` title (the issue title carries it). Turn its relative links into permalinks at the same SHA. Turn a dependency on another spec into its issue reference (`#123`).
3. Anything the index said about this spec that the spec itself does not (its phase, a dependency), as one short line at the end.

Check the title and body for secrets and private details before you create each one: `gh issue create --title "<title>" --body-file <file> [--label <label>]`.

Then verify each one: `gh issue view <n> --json title,body,labels`, and compare the body with the file you wrote, ignoring trailing newlines and `\r` (GitHub and `--jq` add them). If one is wrong, fix it with `gh issue edit <n> --body-file <file>`. Never create a second issue for it.

## 5. Retire the source

- **Spec files:** on a branch, delete the files and the index. Replace every link to them (`grep -rn` for the folder and file names) with the issue link. Where the docs said planned work lives in that folder, say it lives in the issues. Commit, and open the PR with [open-pr](../open-pr/SKILL.md) when the user asked for one.
- **A bundle issue:** comment with the new issues, one link per spec, then close it: `gh issue close <n> --reason "not planned" --comment "<links>"`. Close it only after every new issue is verified.

## 6. Reply

- Each spec and its issue link, marked created or reused.
- Specs deleted with no issue because they shipped.
- The files removed and links repointed, or the bundle issue closed.
