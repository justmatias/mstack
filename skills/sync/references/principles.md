# Cross-cutting principles

Two principles: **English only**, and **Practices, not domain**.

Every mstack skill, every reference and every subagent prompt follows these two principles. They take priority over any other step.

## 1. English only

Everything you write or generate is in English. Never Spanish, never any other language:

- prose rules (`.mdc`), YAML `message` and `note` fields, test cases, code, identifiers and comments;
- commit messages, PR descriptions, issues, `rule-exception` reasons;
- your replies to the user while running the skill.

When a source is not in English (for example a team rule written in Spanish), read it as-is, but write everything you generate from it in English. Never translate a team file without approval: propose the translation in the sync plan instead. Before you propose anything, reread what you generated and rewrite any non-English text.

## 2. Practices, not domain

These skills run in work repos. Extract coding practices only, never domain or business information.

| May be extracted (practices) | Never extracted (domain) |
| --- | --- |
| Language constructs, libraries and frameworks (`@dataclass`, `requests`, `print`) | Business entities and names (classes, functions, modules, tables or fields named after the domain) |
| Patterns and anti-patterns (swallowed exceptions, verbose constructors) | Business rules, flows, calculations, thresholds or concrete values |
| Architecture in generic terms (`domain` does not import `infra`) | Names of clients, products, projects or teams |
| Naming, error-handling, logging and testing conventions | URLs, hosts, endpoints, emails, credentials or internal identifiers |
| Generic folder structure (`src/`, `tests/`, `domain/`) | Repo code snippets copied verbatim, data, or ticket contents |

Operating rules:

1. **Abstract before writing.** Rewrite every learning or mistake class as a generic practice. If it cannot be expressed without the domain, drop it and report it as `dropped: domain-dependent`.
2. **Synthetic tests.** Test cases, including the "real past mistake", are minimal snippets with generic names (`Foo`, `Item`, `User`, `do_work`). Keep the *structure* of the mistake, never its content.
3. **Generic patterns.** YAML rules never match domain identifiers. `files`/`ignores` of repo rules use only structural folders (`**/domain/**`), never business-named modules. Personal rules contain no repo paths at all.
4. **Evidence by reference.** Justify a rule with a commit sha, a PR number or a transcript message index. Never copy their content. Reviewer subagents may read the repo and transcripts, but return only abstracted findings.
5. **Automated verification.** Run `mstack leak-check` over everything you generated before proposing it (see `authoring-a-check.md`). If it flags something, rewrite or drop it. Never ignore a finding.
6. **Transparency.** Your reply lists what was abstracted and what was dropped as domain-dependent.
