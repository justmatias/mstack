---
name: blast-radius
description: "Find what a change could break outside its own diff before it ships, and prove the one fact its safety rests on by running real code instead of arguing it. Reports what the change really does, that fact with its proof, the confirmed risks, what was checked and cleared, and the cheapest test to run before merging. Use for /blast-radius, blast radius of X, what could this break, or a small diff you don't trust yet."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/blast-radius in cursor/plugins (https://github.com/cursor/plugins/tree/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/skills/blast-radius). Thanks to Lauren Tan for the original."
  upstream-commit: "d42aff08aa58965d2735c4ead61a9af82b89d0d0"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/LICENSE"
---

# Blast radius

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the writeup and the proof script, even when the code or the discussion is not. (2) **Practices, not domain**: the writeup cites `file:line` and describes how things break; it never copies business rules, values, URLs or data beyond what a risk needs, and the proof script uses generic names. Details: [../sync/references/principles.md](../sync/references/principles.md).

Find what a change breaks somewhere else, before it ships. [`how`](../how/SKILL.md) says what the code does and [`why`](../why/SKILL.md) says why it is shaped that way; this skill says what the change breaks elsewhere. [`diff-review`](../diff-review/SKILL.md) checks a diff against the rules and the spec; this one looks past the diff.

Listing the callers is not the job: grep does that in a second. The job is the breakage grep does not show.

## Prove, don't argue

A writeup that sounds right reads the same whether or not it is true. So find the one or two facts the change's safety depends on and prove them. For each, get it as far down this ladder as is cheap, and say where it stopped:

1. **Said so.** Worth nothing on its own.
2. **Pointed at the line.** A real `file:line`, in this repo or in the library's own source.
3. **Walked the bad case.** You traced the failure step by step and it cannot be reached.
4. **Ran it.** A small script or test that calls the real code and fails loudly if you are wrong.
5. **Reproduced it** in the running app.

Step 4 is usually one short script that imports the same library version the app ships and calls the exact function you are worried about.

## Steps

1. **Read the change.** The diff, the symbols it adds, changes and removes, and what it now does differently, including the part the diff does not spell out. Read the PR and its commits when there is one.
2. **Find the fact it is safe because of.** Most changes that look risky are safe because of one fact, such as "this call only drops cache entries nothing reads any more". If that fact holds, most risky cases clear at once. Spend your time here, not on a long list of maybes.
3. **Look where grep stops.** Read the source of the libraries the change calls, at the pinned version, including any local patch. Work out when things run: async callbacks, teardown and shutdown, framework lifecycles. Follow what a symbol search misses: serialized payloads and API responses, database columns, wire formats, another language reading the same bytes, feature flags, code a few hops downstream.
4. **Weigh each risk honestly.** Give it a real likelihood and a real cost. Keep the confirmed risks, and list the ones you checked and cleared separately. Cite a real `file:line`; a search that finds nothing is still an answer. Never invent a caller or an API.
5. **Prove the fact.** Write the script or test, run it, and paste what happened.
6. **For a big or wide change,** run [`review-loop`](../review-loop/SKILL.md) on the same question with a reviewer from another model family, and merge what it finds into the writeup. Different models catch different real bugs.

## Reply

- **What it does.** What changed, including the part that is not obvious.
- **The fact it is safe because of.** State it, name the ladder step it reached, and show the proof. If you could not prove it, write **unproven**.
- **Risks.** Each names how it breaks, the `file:line`, how likely and how bad, and how to check. Paste the proof for the ones that matter.
- **Cleared.** What you checked and why it is fine.
- **Before you merge.** The cheapest test or repro that would catch the real bug, including the script you wrote.

Write it through [`unslop`](../unslop/SKILL.md), and strip anything private before it goes anywhere public.
