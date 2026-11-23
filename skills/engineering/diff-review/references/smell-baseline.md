# Smell baseline

> **Principles (always apply):** (1) **English only**: every finding is written in English. (2) **Practices, not domain**: a finding names the smell and the hunk, never the business rule behind it. Details: [../../sync/references/principles.md](../../sync/references/principles.md).

A fixed set of code smells, after Martin Fowler's *Refactoring* (chapter 3), that the Standards axis checks even in a repo that documents nothing. Two rules bind it:

- **The repo wins.** A documented repo rule always overrides a smell. Where a rule endorses what a smell would flag, drop the smell.
- **Always a judgment call.** Report a smell as "possible <smell>", never as a violation, and skip anything a linter already enforces.

Each line: what to look for in the diff → the usual fix.

| Smell | What to look for | Usual fix |
| --- | --- | --- |
| Mysterious Name | A function, variable or type whose name does not say what it does or holds | Rename it; if no honest name fits, the design is unclear |
| Duplicated Code | The same logic shape in more than one hunk or file of the change | Extract the shared part and call it from each place |
| Feature Envy | A function that uses another object's data more than its own | Move it next to the data it uses |
| Data Clumps | The same few fields or parameters always passed together | Group them into one type and pass that |
| Primitive Obsession | A string or number standing in for a concept that deserves a type | Give the concept a small type of its own |
| Repeated Switches | The same `switch` or `if` chain on the same value in several places | One mapping both places share, or polymorphism |
| Shotgun Surgery | One logical change forces small edits across many files | Gather what changes together into one module |
| Divergent Change | One module edited in the change for several unrelated reasons | Split it so each part changes for one reason |
| Speculative Generality | Parameters, hooks or abstractions for needs the spec does not have | Remove them until a real need appears |
| Message Chains | Long `a.b().c().d()` navigation the caller should not depend on | Hide the walk behind one method on the first object |
| Middle Man | A class or function that mostly forwards calls | Remove it and call the real target |
| Refused Bequest | A subclass or implementer that ignores or overrides most of what it inherits | Use composition instead of inheritance |
