---
name: architect
description: "Sketch the types, signatures and module boundaries of a change before writing code, compare two shapes, and pick the one with the clearest ownership; then stay in the loop while the implementation fills it in. Use for /architect, architect this, design this, or non-trivial work where jumping straight to code would lock in the wrong shape."
disable-model-invocation: true
license: MIT
metadata:
  adapted-from: "pstack/skills/architect in cursor/plugins (https://github.com/cursor/plugins/tree/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/skills/architect). Thanks to Lauren Tan for the original."
  upstream-commit: "d42aff08aa58965d2735c4ead61a9af82b89d0d0"
  upstream-license: "MIT, Copyright (c) 2026 Lauren Tan, https://github.com/cursor/plugins/blob/d42aff08aa58965d2735c4ead61a9af82b89d0d0/pstack/LICENSE"
---

# Architect

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, including the sketches and their names, even when the task is not. (2) **Practices, not domain**: the sketch describes structure (types, signatures, owners, boundaries); it never copies business rules, values or URLs beyond what the design needs. Details: [../sync/references/principles.md](../sync/references/principles.md).

Design the shape of a change before any code exists, so the code has one obvious place to go.

1. **Trace what it touches.** Read every module, type and caller the change reaches, using [`how`](../how/SKILL.md) when an area is unfamiliar. Write down where each piece of state the change reads or writes lives today.
2. **Sketch two different shapes.** Two shapes that differ in where state lives or where a boundary falls, not two spellings of one idea. Each sketch lists the types, the function signatures and which module owns what. Leave the bodies empty.
3. **Pick one.** Prefer the shape where each piece of state has one owner, each task has one way to do it, and callers need to know the least. Say in one line why the other lost.
4. **Show it and wait.** Show the chosen sketch with that line. Write code only after the user agrees, or after they say to go ahead without asking.
5. **Stay in the loop.** While the implementation fills in, compare it with the sketch. When it needs a workaround the sketch did not foresee, and the same kind of workaround comes up again, stop and redesign the sketch instead of patching around it.

For a large or contested design, run [`grill-me`](../grill-me/SKILL.md) on the chosen shape before writing code.
