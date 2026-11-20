# Authoring a check

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, even when the source is not. (2) **Practices, not domain**: extract coding practices only, never business names, rules, values, URLs or verbatim repo code. Details: [principles.md](principles.md).

The recipe for turning one checkable prose rule into a check. `sync`, `reflect` and `correct` all follow it.

The checks run through the `mstack` command on `PATH`: `mstack lint` runs every step (ast-grep tests and scan, import-linter, and the `coverage`, `exceptions` and `leak-check` guards), and `mstack <command> --help` lists the options. It works from any repo and needs nothing installed in the repo's own environment: ast-grep and import-linter ship with it. If `mstack` is not found, ask the user to install it from their mstack checkout with `uv tool install --editable <checkout>`; do not look for the scripts on disk. The commands read the repo's paths from `.mstack.toml` when it exists; run `mstack config` to see them. Paths below use the defaults: replace `lint-rules/` with the folder of the configured sgconfig (default `lint-rules/sgconfig.yml`), and `.cursor/rules/` with the configured `rules_dir`. Pass paths in the work repo as absolute paths or relative to the current directory.

## 0. Static check or LLM review?

Decide this before you pick a tool. A static check costs a YAML file, its tests, its false positives and every exception people add to dodge it, so it has to be worth that. A rule with `enforcement: llm-review` costs only its prose: the reviewer reads it on every PR.

Write a **static check** only when every one of these holds:

- **The bad code is a concrete construct**: a call, a decorator, an import, a statement shape. You can show it in one line and say "never this".
- **The file alone decides it.** No intent, naming, call sites in other files or runtime data is needed to tell a violation from fine code.
- **One simple rule expresses it**: one ast-grep pattern with at most a `not`, `inside` or `has` or two, or one import-linter contract. No Fixit or custom logic.
- **Near misses are easy to tell apart.** You can write the valid near-miss cases, and the scan finds no false positive you cannot remove without narrowing the rule until it misses the real mistake.
- **The message names one fix** ("use `Foo` instead"), not "it depends".

Use **rule + `enforcement: llm-review`** when any of these holds:

- It is about meaning: names, responsibilities, "a function does one thing", when to use an abstraction.
- Expressing it needs a chain of exclusions, several rules for one idea, a Fixit codemod, or cross-file knowledge.
- You expect legitimate exceptions to be common (more than a few `ast-grep-ignore` lines).
- The tests pass only because the cases were tuned to the pattern, not because the pattern matches the mistake.

**Borderline: ask the user.** When the rule fails one static criterion but not clearly, or the check needs Fixit, do not decide alone. Show both options side by side: the check you would write (tool, pattern sketch, scan count, expected exceptions) and the llm-review rule, with your recommendation. Let the user pick. The user may also override either default; record their choice in your reply.

## 1. Pick the tool

Only for rules that passed step 0. Try them in this order and stop at the first that expresses the rule without false positives:

| Tool | Use it for | Example |
| --- | --- | --- |
| ast-grep (YAML in `lint-rules/rules/`) | Code patterns | no `print`, no `@dataclass`, no bare `except:` |
| import-linter (`.importlinter`) | Dependencies between modules | `domain` does not import `infra` |
| An existing linter run as a pre-commit hook (`enforced-by-hook: <id>`) | What a dedicated tool already checks | shellcheck for unquoted expansions, gitleaks for committed secrets, a commit-message check |
| Fixit (LibCST, Python) | Logic a pattern cannot express, only after the user chose it in step 0 | an `__init__` that only assigns `self.x = x` across a whole class |
| none: `enforcement: llm-review` | Judgment | descriptive names, single-purpose functions |

A hook goes in `.pre-commit-config.yaml` pinned to a full tag or sha (in the mstack repo, `hookpin` checks the pins); write `- enforced-by-hook: <hook id>` in the Checks section, and skip steps 2 to 6.

If no tool fits, or the check grows past what step 0 allows, the rule is judgment: mark it `enforcement: llm-review` and stop. Do not force a pattern at the cost of false positives; a narrower check shipped as `warning` is better than a broad one that people learn to ignore.

## 2. Write the YAML

`lint-rules/rules/<id>.yml`, one rule per file, `id` in kebab-case and equal to the file name:

- `id`, `language`, `severity`, `message` (what to use instead), `note` (why), `metadata.source` (the `.mdc` path from the repo root), and `files`/`ignores` only with structural globs (`"**/domain/**"`).
- Find node names with `ast-grep run -l <language> -p '<snippet>' --debug-query=ast`. Python facts: a bare `except:` is an `except_clause` with no `value` field; `kind` does not take a regex; a pattern such as `self.$A = $A` matches the `assignment` node, not its `expression_statement`. Bash facts (`language: Bash`): a call is a `command` whose `name` field is the program (`has: {field: name, regex: "^eval$"}`); `$(...)` and backticks are both `command_substitution` (tell them apart with `regex: "^\`"`); a script's top-level commands are direct children of `program`.
- Quote a YAML string that contains `: ` or starts with a backtick.
- The pattern never names a domain identifier. Match the construct (`print($$$ARGS)`), not a business class.

For an import-linter contract, add a `[importlinter:contract:<id>]` section with `name = <id>` to `.importlinter`; the section id is what `enforced-by:` refers to.

## 3. Write the tests

`lint-rules/rule-tests/<id>-test.yml` with at least 2 `valid` and 2 `invalid` cases:

```yaml
id: <id>
valid:
  - |
    <code that follows the rule, including a near miss>
invalid:
  - |
    <the real mistake, rewritten as a synthetic snippet>
  - |
    <a variant of the mistake>
```

- One invalid case is based on a **real mistake**. Find it with `git log -S '<construct>' --oneline` or `git log -G '<regex>'`, read it with `git show <sha>`, and **rewrite it as a synthetic snippet with generic names** (`Foo`, `Item`, `User`, `do_work`). Keep its structure, never its content. Cite the sha in your reply, never in the test file.
- With no real mistake in history, write the most likely shape of it, and say so in your reply.
- Valid cases include near misses (a method named `print` on another object, a typed `except` with `pass`) so the rule does not over-match.

For an import-linter contract, the "test" is proving the contract breaks: copy the offending module into a temporary copy of the package and confirm `lint-imports` reports the contract as `BROKEN`.

## 4. Run the tests

```bash
mstack lint --only test
```

It runs `ast-grep test --skip-snapshot-tests` with the configured sgconfig (default `lint-rules/sgconfig.yml`). Iterate until it passes. `--skip-snapshot-tests` still fails when a valid case matches or an invalid case does not; it only skips label snapshots.

## 5. Measure existing violations

```bash
mstack lint --only scan --json
```

The scan skips the `[scan].exclude` globs. Count the findings whose `rule` is `<id>` and look at each one: is it a real violation or a false positive? Fix false positives in the rule (back to step 2).

## 6. Pick the severity

- `error` if there are 0 violations, or you fix all of them in the same change.
- Otherwise `warning`, plus a migration issue. `mstack lint --changed` (and `make lint-rules-changed`) passes `--error` to ast-grep, so a `warning` rule still fails on new or touched code; only the old instances are tolerated.

Never ship as `error` a rule that would break `main` on the next CI run.

## 7. Update the Checks section

Add `- enforced-by: <id>` to the `.mdc` named in `metadata.source`. If the rule changed meaning, update or delete the old YAML instead of adding a second one.

## 8. Verify what you generated

```bash
mstack leak-check <every file you generated> --repo .
```

`--repo` defaults to the git root, and `[leak_check].exclude` in `.mstack.toml` lists tooling folders that are not analyzed code; in the mstack repo itself, a bare `mstack leak-check` checks the right paths. If it flags anything, rewrite it as a generic practice or drop it. Then reread everything you generated and confirm it is entirely in English.

## 9. Run the single command

```bash
mstack lint
mstack lint --changed   # only the changed files, warnings included
make demo               # only in repos that have fixtures/invalid/
```

A repo with `make lint-rules` targets may call them instead; they run the same command.

Commit the YAML, its tests and the `.mdc` together, one commit per rule, with a Conventional Commits message (`feat(rules): add <id> check`).

## Adopting in a repo with no `lint-rules/`

Before the first check, scaffold the layout with `mstack init`. Run `mstack init --dry-run` first (add `--pre-commit`, `--ci github` or `--makefile` for the optional pieces, and `--rules-dir` or `--checks-dir` when the repo keeps them elsewhere), show the user its plan, and run it with `--yes` only after they approve. It writes `.mstack.toml`, `lint-rules/sgconfig.yml` with empty `rules/` and `rule-tests/`, and the rules folder; it never overwrites a file, and an empty layout passes `mstack lint`.
