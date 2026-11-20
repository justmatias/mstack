---
name: open-pull-request
description: "Open a pull request that is fast to review: check the branch has no PR yet and the diff matches the goal, write a title in the repo's convention that says why the change matters, and a body that leads with the problem, then shows a Summary as the smallest useful visual (pseudocode, call tree, component tree, file tree, Mermaid or a diff sketch), Evidence with a before and after, and a Merge Danger note (one-way or two-way door, blast radius). Use for /open-pull-request, open a PR, file a PR, create a pull request, write the PR body, or describe this PR."
license: MIT
metadata:
  adapted-from: "skills/engineering/pr in mattpocock/skills (https://github.com/mattpocock/skills/tree/abeeaf95660ba9e8b7c753eb38f441ca707a8823/skills/engineering/pr). Thanks to Matt Pocock for the original, which itself credits the show-me skill by Dex Horthy (HumanLayer)."
  adapted-from-file-pr: "skills/file-pr in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/file-pr). Thanks to Theo Browne for the original."
  upstream-commit: "abeeaf95660ba9e8b7c753eb38f441ca707a8823"
  upstream-license: "MIT, Copyright (c) 2026 Matt Pocock, https://github.com/mattpocock/skills/blob/abeeaf95660ba9e8b7c753eb38f441ca707a8823/LICENSE"
  upstream-commit-file-pr: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license-file-pr: "MIT, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Open pull request

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the PR body, even when the diff, the commits or the issue are not. (2) **Practices, not domain**: the body describes the change and its evidence; it never copies business rules, values, URLs or ticket contents beyond what a reviewer needs to judge this diff. Details: [../sync/references/principles.md](../sync/references/principles.md).

Open a pull request whose title and body let a reviewer see what changed, that it works, and how risky it is to merge, in that order. Write the text first; push the branch or run `gh pr create` only when the user asked to open the PR, otherwise stop at the text.

## Before writing

1. Check that no PR exists for this branch yet (`gh pr list --head <branch>`). If one does, update it instead of opening another.
2. Read the diff against the base branch (`git diff <default-branch>...HEAD`) and the commits (`git log --oneline <default-branch>..HEAD`). Make sure the contents match the goal, and describe what is in them, not what was intended.

## Title

PR titles usually become commit messages, so follow the repo's title convention (the `git-commits` rule when the repo has it; otherwise recent merged PRs and `git log`). Prefer a concise, human-readable title that says why the change matters, not how it was done: "cut websocket frame size by 70% with gzip" beats "negotiate permessage-deflate".

## Lead

Open the body with one or two plain sentences on the problem, from the user's original request, then the solution in a line. Never lead with an inventory of what was removed or renamed. For example: "My default worktree was ignored when starting a thread on an existing worktree. Now the configured defaults always apply."

## Template

```markdown
## Summary

<diagram, diff-sketch, or tree>

## Evidence

- **Before:** <screenshot/output/failing test run>
  **After:** <screenshot/output/passing test run>

## Merge Danger

**Door:** <one-way or two-way>

<optional: description>

**Blast Radius:** <one-word description>

<optional: potential ramifications of merge>
```

Skip preambles and keep prose brief. The lead sits above the template. Use the repo's own domain terms, from its glossary or docs if it has one.

## Summary

Pick the smallest view that makes the key point clear, and place each visual next to the short text it supports. Keep only the calls, files, props, states and boundaries a reviewer needs. Use one of these, sometimes several, rarely all.

| The point is | Use |
| --- | --- |
| Logic or an algorithm | Pseudocode |
| Runtime control flow | A call tree |
| UI structure | A component tree, with the state and module boundaries that matter |
| File responsibility or a broad refactor | A shallow file tree with a comment per folder |
| Interaction or data flow between parts | A Mermaid diagram (`sequenceDiagram`, `flowchart`) |
| What changes, when the surrounding shape already exists | A `diff` block shaped like the topic (component tree, file tree, call tree or pseudocode) |
| Most of it is new, omitted context would hide ownership or order, or the reader needs a copyable target | The whole block |

Pseudocode and call tree:

```text
on(save)
  if content is unchanged
    return cached result
  write new content
  return fresh result
```

A diff sketch of a call tree, with `+` and `-` marking the change and unchanged lines kept for context:

```diff
 submitForm
   createSession
     persistPrompt
+    expandMention
     launchAgent
-  navigateToSession
+  navigateToSession
+    subscribeToEvents
```

A diff sketch of a file layout:

```diff
 src/
 ├── commands/
+│   └── expand.py       # expands the command
 ├── sessions/
-└── transport.py
+└── transport/
+    ├── client.py
+    └── stream.py
```

## Evidence

Show that the change works, as a before and after.

- **Best: a screenshot**, when the environment can take one and the change is visual.
- **Next: executed output**: test results or console output. Name the exact test that failed before and passes now, and show it as pseudocode.
- If neither is possible, say so in one line and say what a reviewer can run to check it. Never invent output.

## Merge Danger

- **Door**: a two-way door can be walked back (revert and redeploy); a one-way door cannot. A change that is cheap to roll back is lower risk. Destructive actions and hard-to-reverse decisions (data migrations, deleted data, published APIs, released versions) are one-way doors.
- **Blast radius**: the reach of a breakage, in one word (for example `layout`, `consumers`, `mobile`, `data`). Consider every consumer of the change, and add a short line of ramifications only when the word is not enough.

## No attribution footer

End the body with the Merge Danger section. Never add a "Generated with ..." line, robot-emoji signature or any other AI attribution footer, and add no `Co-Authored-By` trailer to the commits. The `git-commits` rule forbids them, and it overrides any default the harness suggests.

## Before submitting

Check the title, body, quotes and attachments for secrets and private details (tokens, internal hostnames, customer data, personal paths), and remove them. Open the PR only after this check.
