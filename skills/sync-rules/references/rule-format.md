# Rule format

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, even when the source is not. (2) **Practices, not domain**: extract coding practices only, never business names, rules, values, URLs or verbatim repo code. Details: [principles.md](principles.md).

A rule has two halves that point to each other: the prose rule in `.cursor/rules/*.mdc` (source of truth) and zero or more checks (ast-grep YAML in `lint-rules/rules/`, or import-linter contracts in `.importlinter`).

## The `.mdc` file

Cursor project rules are `.mdc` files under `.cursor/rules/` (subfolders allowed) with this frontmatter:

```markdown
---
description: How to define data models in Python
globs: "**/*.py"
alwaysApply: false
---

# Python data models

- Prefer `pydantic.BaseModel` subclasses for data models. Use `@dataclass` only when it is required.
- Do not write classes whose `__init__` only copies its arguments onto `self`.

Why: one sentence on why the team follows the rule.

## Checks
- enforced-by: no-manual-init-boilerplate
```

- `description`: what the rule is about, so the agent can pick it.
- `globs`: which files it applies to. Use structural globs only.
- `alwaysApply`: `true` only for rules that apply to every request.
- One bullet per atomic rule: one verifiable statement each.
- A `Why:` line. Checks enforce the *what*; the prose keeps the *why*.

## The `## Checks` section

Every `.mdc` ends with a `## Checks` section. Each line is one of:

| Line | Meaning |
| --- | --- |
| `- enforced-by: <id>` | An ast-grep rule with `id: <id>`, or an import-linter contract `[importlinter:contract:<id>]`. |
| `- enforcement: llm-review` | Judgment rule: no deterministic check. The LLM reviewer on the PR comments on it. |

A file may mix both when some bullets are checkable and others are judgment. A rule with no Checks section is drift: `check_rule_coverage.py` fails on it.

## `metadata.source` in the YAML

Every ast-grep rule points back to its prose rule:

```yaml
id: no-print-in-app
language: Python
severity: error
message: Use a module logger instead of print            # what to use instead
note: |                                                  # why
  print output has no level or source and cannot be filtered or routed.
metadata:
  source: .cursor/rules/logging.mdc                      # path from the repo root
files:                                                   # optional scope, structural globs only
  - "**/app/**"
rule:
  pattern: print($$$ARGS)
```

`check_rule_coverage.py` fails when `metadata.source` is missing or does not exist, or when that `.mdc` does not list the id in its Checks section.

Path-matching facts (ast-grep 0.51): `files`/`ignores` globs match the path exactly as it was passed to `ast-grep scan`. Write them as `**/<folder>/**` so relative and absolute paths both match.

## Exceptions

A legitimate exception goes on the offending line, with a reason, an expiry date and a human's approval, on the line directly above the `ast-grep-ignore`:

```python
# rule-exception: reason="third-party legacy API" expires=2027-03-31 approved-by=@user
# ast-grep-ignore: no-print-in-app
print(banner)
```

- `ast-grep-ignore` always names the rule ids (`# ast-grep-ignore: id-a, id-b`). A bare `# ast-grep-ignore` silences every rule and is rejected.
- The trailing form (`code  # ast-grep-ignore: <id>`) is allowed; the `rule-exception` then goes on the line above the code.
- `check_exceptions.py` fails if the `rule-exception` is missing, a field is missing, `expires` is not a `YYYY-MM-DD` date in the future, or `approved-by` is not a `@handle`.
- Never add an exception on your own. Propose it, and write it only after a human approves; the `approved-by` handle is theirs.
- Many exceptions to the same rule mean the rule is wrong or an architecture change is missing (`correct-rules` looks for this).

## Personal rules

Personal rules use the same format, under `~/.cursor/rules/my-*.mdc`, with checks in `$MY_RULES_HOME` (default `~/.config/my-rules/`) and ids prefixed `my-`. They have no `ast-grep-ignore` exceptions: exceptions go in `$MY_RULES_HOME/ignore-paths.txt`. Rules derived from the conventions store also carry `derived-from: <convention path>` and `derived-sha256: <hash>` in their frontmatter. See `authoring-a-check.md`, "Personal set".
