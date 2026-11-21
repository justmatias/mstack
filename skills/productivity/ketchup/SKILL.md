---
name: ketchup
description: "Catch the user up on what changed in this chat since their last message, in plain words and small visuals, then list every call waiting on them with what they need to make it from the reply alone (link, what it changes, evidence, risk and a recommended pick). Read-only. Use for /ketchup, catch me up, what happened while I was away, or what do you need from me."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/ketchup in cursor/plugins (https://github.com/cursor/plugins/tree/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/skills/ketchup). Thanks to Lauren Tan for the original."
  upstream-commit: "d42aff08aa58965d2735c4ead61a9af82b89d0d0"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/LICENSE"
---

# Ketchup

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the catch-up and its visuals, even when the chat is not. (2) **Practices, not domain**: the catch-up says what changed for the user and what waits on them; it never adds business data, values or URLs beyond what a call needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Catch the user up on what changed in this chat since the last message they wrote before `/ketchup`, so they understand each change and not only where it stands. Then lay out every call waiting on them so they can make it from your reply alone. Notifications and subagent results are not their messages. Assume they remember their last message and nothing after it.

This is not [`recall`](../recall/SKILL.md), which rebuilds context across sessions, nor [`handoff`](../handoff/SKILL.md), which writes a brief for another agent.

Use [`bro`](../bro/SKILL.md)'s voice: plain words, short sentences, no jargon, like one person catching up another. Say what changed for the user, not how you did it: "the tests pass", not "CI is green". Leave out hashes, file paths, commands, build numbers and test counts unless the user needs one to act. Call each PR, branch or agent by a name the user would know, not a label you invented. If a fact needs context to make sense, give the context or leave the fact out.

## Gather what changed

Keep this turn read-only: do not change code, start an app or a job, or post anything, and make visuals only from what you already have. Collect your own work since that message, subagent reports, and messages from anyone else in the chat. Check the current state of each PR, CI run or agent this chat touched. Check each number you will show against its source, and say so when you correct one.

An **action item** is a call or step only the user can take: a product choice, an approval, an irreversible action, or access you lack. Include every one still waiting, even one raised before their last message. Work you can still do yourself is not an action item. Never invent a call to fill the reply. A step the user did not ask for and the work does not need is not an action item, unless it is irreversible and waiting on them: then it gets one line and no visual.

One call can cover many items, such as each PR in a set awaiting merge. For each item collect its link, what it changes for users, the evidence behind your pick, its risk, and your pick. Write "unknown" for a fact the call needs that you do not have. Leave out links you do not have.

## Write the reply

Spend words on the calls, not on the story.

1. **Open** with one short sentence naming what waits on the user, or saying nothing does. If nothing happened and nothing waits, say so and stop.
2. **What happened, pictures first.** Embed the screenshots and videos the work produced, then any diagram that explains a change. Then one short bullet per thing the user asked for: what came of it, and whether it is done, still running, failed or not checked. Write each line as you would say it aloud ("Search was slow because of a missing index", not "Search review: done"). Name any bug found and fixed on the way. Each line stays true read alone. Never mark something done that still waits on the user, and leave out what the action items cover. Keep this part under 100 words, not counting pictures, and shorter when less happened. Then at most three lines that change what the user knows or must do, and one line on work left that you can do yourself.
3. **Action items.** Ask the call the user owns (merge, approve, pick) and give your pick. A step you would take first goes in the pick, as does anything that must happen first and anything that cannot be undone. Give each PR, issue or agent's number or link. About 30 words per item; the reply grows with the number of items, and you never cut or merge items to save words: no count in place of a list, no link in place of an item.
   - A call about one item is one bullet: the call, your pick, what it changes for users, the evidence, and its risk.
   - When items share a call, write the call and pick once, then one bullet per item, riskiest first: link and name, what it changes, the evidence and its risk. Name an item's pick only where it differs.
   - Give every item's risk, even a low one ("Low risk: only the colors change"). Say what waiting costs only when it is more than a delay, such as a deadline or lost data.
   - For a call between options, give every option you weighed, each with what it gets the user and what it costs, and the current state when there is one. Those costs are the risk, so add no separate risk line.

## Visuals

A visual is a picture: a screenshot, a video, a Mermaid diagram, a chart, or a page from [`show-me`](../show-me/SKILL.md). A Markdown table is not a visual.

Draw when a picture is easier to grasp than sentences: how a design or system works, a PR stack with each PR's state, a before and after of a fix, or options side by side. Never draw a status list, a list of action items, or boxes with nothing connecting them, and never give a fact twice.

Keep each visual readable at a glance: at most six boxes, at most eight words in each, labels in plain words. Embed screenshots and videos inline when a change is visible; if a visible change has none, mark its line "No screenshot yet" and say what changed on screen. Never invent a number, never draw a screen you did not capture, and link only artifacts that exist.
