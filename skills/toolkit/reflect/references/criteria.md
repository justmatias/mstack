# Reflect: what to keep, and the output format

> **Principles (always apply):** (1) **English only**: every finding and every cell you write is in English, even when the transcript is not. (2) **Practices, not domain**: keep only generic coding practices; reject with reason `domain` anything that cannot be expressed without business names, rules, values, client, product or team names, URLs, emails, credentials or repo code. Evidence is cited by message index, never copied. Details: [../../sync/references/principles.md](../../sync/references/principles.md).

## Kinds of coding convention

| Kind | Means | Ends up as |
| --- | --- | --- |
| **pattern** | A concrete construct one simple ast-grep rule can deny from the file alone, with no false positives | Prose rule + ast-grep check |
| **architecture** | A dependency between modules one import-linter contract can deny | Prose rule + import-linter contract |
| **judgment** | Anything else, including what a tool could check only with complex logic, cross-file knowledge or many exceptions | Prose rule with `enforcement: llm-review` |
| **borderline** | Fails one of the static tests, but not clearly | Both options prepared; the user picks |

For pattern and architecture, name the generic construct to match ("a call to `datetime.now()` with no `tz` argument"), never a domain identifier.

## Criteria for every finding

- **Durable:** still true in six months, once paths, SHAs, versions and code shapes have changed.
- **Specific:** broad enough to apply across tasks, precise enough that a future agent recognizes when to use it. Reject platitudes ("write good code") and one-off facts ("this skill has 175 tokens").
- **Decision-changing:** a future agent does something different because of it, not just reads more text.
- **Checked when possible:** a finding a lint or contract could enforce becomes a `rule:` row with its kind, never Backlog. Skill prose is for workflow, not for coding conventions.
- **Existing rule first:** edit the related `.mdc` rather than adding a duplicate. A finding that contradicts an existing rule is a `conflict` row with both side by side; never resolve it yourself.
- **Existing skill first:** a skill edit routes only to a skill the session used. A skill that should have fired but did not gets `tune description:`. A new skill only when no existing one is a real home and the pattern recurs.
- **Not already covered:** read the target skill or rule first. If it already says this clearly, reject as `already-covered`; if it says it weakly or where it is easy to miss, propose a wording or placement change instead of a duplicate.

## Output

No preamble. One sentence per cell.

### Accepted

| Problem | Proposal | Routing | Kind |
| --- | --- | --- | --- |
| A coding convention from the chat | Prose rule + check: the generic construct | `rule: <rules_dir>/<file>.mdc` or `new: <name>` | pattern / architecture / judgment / borderline |
| A finding that contradicts an existing rule | `conflict:` existing rule (path:line) vs the proposed one | `rule: <path>` | kind |
| A failure mode in a skill the session used | The change to that skill's body | Skill path and section | - |
| A skill that existed but did not trigger | Tune its description so it fires next time | `tune description: <skill path>` | - |
| A new pattern with no existing home | Draft a new skill | `new skill: <kebab-name>` | - |

### Rejected

One line each: the principle, and the reason (`durability`, `specificity`, `decision-changing`, `duplicate`, `already-covered`, `skill-not-used` or `domain`).

### Backlog

Only what no available tool can check, or what needs a large architecture change: the generic pattern, where it was hit (message index), and the suggested mechanism.

<!-- Adapted from pstack/reflect (MIT). Attribution in the reflect SKILL.md frontmatter. -->
