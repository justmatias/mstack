---
name: leave-pr-comments
description: "Leave comments on GitHub (top-level PR comments, inline review comments, replies to reviewers or bots, and explanations posted before resolving feedback) so a reader can tell an agent wrote them on the user's behalf: a note callout names the model and the user, the reply sits outside it, the text is checked for secrets, written conclusion-first, previewed, and verified after posting. Use for /leave-pr-comments, comment on this PR, reply to the reviewer, respond to review feedback, answer this thread, or any time you are about to post a comment on GitHub."
license: MIT
metadata:
  adapted-from: "skills/leaving-pr-comments in t3dotgg/tstack (https://github.com/t3dotgg/tstack/tree/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/skills/leaving-pr-comments). Thanks to Theo Browne for the original."
  upstream-commit: "11e37a74d0a6868c121cd0910ab2b3bd9873b92a"
  upstream-license: "MIT, Copyright (c) 2026 Theo Browne, https://github.com/t3dotgg/tstack/blob/11e37a74d0a6868c121cd0910ab2b3bd9873b92a/LICENSE"
---

# Leave PR comments

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the comment, even when the PR, the thread or the code is not. (2) **Practices, not domain**: a comment cites the code, behavior or check a reviewer needs to judge the point; it never copies business rules, values, URLs or private details beyond that. Details: [../sync/references/principles.md](../sync/references/principles.md).

Post comments that say who wrote them, lead with the answer, and can be checked. Post only when the user asked you to comment or reply; otherwise stop at the text.

## Attribution

Start every agent-written comment with this note callout, then the comment outside it:

```md
> [!NOTE]
> 🤖 **<model> responding on behalf of <user>**

The actual comment starts here.
```

- `<model>` is the verified public name of the model that wrote the comment. If the harness does not expose it, use the harness name (for example "Claude Code"). Never guess.
- `<user>` is the user's name or GitHub login (`gh api user --jq .login`).
- The context line starts with the robot emoji and sits inside the note. Add no horizontal rule, Setext underline, heading, signature footer or second attribution.

Apply it to top-level PR comments, inline review comments, replies to bots or reviewers, and the written explanation you post before resolving or dismissing feedback. Skip it for PR descriptions (see [open-pull-request](../open-pull-request/SKILL.md)), commit messages, and text the user asked to post verbatim without attribution.

## Writing

- Lead with the conclusion.
- Cite the code, behavior, check or reproduction the point rests on.
- Keep it short: no filler, canned thanks or status narration.
- Say which statements you verified and which are judgment.

## Before posting

1. Check the whole comment, including quoted text and attachments, for secrets and private details (tokens, internal hostnames, customer data, personal paths), and remove them.
2. Preview the final Markdown so the quoting and blank lines render as intended, and show it to the user when they have not seen the text yet.

## After posting

1. Check that GitHub returned the comment or review URL, and report it. If it did not, say the post failed and do not retry blindly.
2. Resolve a review thread only after the reply was posted successfully.
