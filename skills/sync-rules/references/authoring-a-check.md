# Authoring a check

> **Principles (always apply):** (1) **English only**: everything you write or generate is in English, even when the source is not. (2) **Practices, not domain**: extract coding practices only, never business names, rules, values, URLs or verbatim repo code. Details: [principles.md](principles.md).

The recipe for turning one checkable prose rule into a check. `sync-rules`, `reflect-rules` and `correct-rules` all follow it.

The guards run through the `mstack` command on `PATH` (`mstack coverage`, `mstack exceptions`, `mstack leak-check`; `mstack <command> --help` lists the options). It works from any repo and needs nothing installed in the repo's own environment. If `mstack` is not found, ask the user to install it from their mstack checkout with `uv tool install --editable <checkout>`; do not look for the scripts on disk. Pass paths in the work repo as absolute paths or relative to the current directory.

## 1. Pick the tool

Try them in this order and stop at the first that expresses the rule without false positives:

| Tool | Use it for | Example |
| --- | --- | --- |
| ast-grep (YAML in `lint-rules/rules/`) | Code patterns | no `print`, no `@dataclass`, no bare `except:` |
| import-linter (`.importlinter`) | Dependencies between modules | `domain` does not import `infra` |
| Fixit (LibCST, Python) | Logic a pattern cannot express | an `__init__` that only assigns `self.x = x` across a whole class |
| none: `enforcement: llm-review` | Judgment | descriptive names, single-purpose functions |

If no tool fits, the rule is judgment: mark it `enforcement: llm-review` and stop. Do not force a pattern at the cost of false positives; a narrower check shipped as `warning` is better than a broad one that people learn to ignore.

## 2. Write the YAML

`lint-rules/rules/<id>.yml`, one rule per file, `id` in kebab-case and equal to the file name:

- `id`, `language`, `severity`, `message` (what to use instead), `note` (why), `metadata.source` (the `.mdc` path from the repo root), and `files`/`ignores` only with structural globs (`"**/domain/**"`).
- Find node names with `ast-grep run -l <language> -p '<snippet>' --debug-query=ast`. Python facts: a bare `except:` is an `except_clause` with no `value` field; `kind` does not take a regex; a pattern such as `self.$A = $A` matches the `assignment` node, not its `expression_statement`.
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
uv run ast-grep test -c lint-rules/sgconfig.yml --skip-snapshot-tests
```

Iterate until it passes. `--skip-snapshot-tests` still fails when a valid case matches or an invalid case does not; it only skips label snapshots.

## 5. Measure existing violations

```bash
uv run ast-grep scan -c lint-rules/sgconfig.yml --filter '^<id>$' --globs '!fixtures/invalid/**' .
```

Count the findings and look at each one: is it a real violation or a false positive? Fix false positives in the rule (back to step 2).

## 6. Pick the severity

- `error` if there are 0 violations, or you fix all of them in the same change.
- Otherwise `warning`, plus a migration issue. `make lint-rules-changed` passes `--error` to ast-grep, so a `warning` rule still fails on new or touched code; only the old instances are tolerated.

Never ship as `error` a rule that would break `main` on the next CI run.

## 7. Update the Checks section

Add `- enforced-by: <id>` to the `.mdc` named in `metadata.source`. If the rule changed meaning, update or delete the old YAML instead of adding a second one.

## 8. Verify what you generated

```bash
mstack leak-check <every file you generated> --repo .
```

In the mstack repo itself, add `--exclude src --exclude scripts --exclude tests` (tooling, not analyzed code). If it flags anything, rewrite it as a generic practice or drop it. Then reread everything you generated and confirm it is entirely in English.

## 9. Run the single command

```bash
make lint-rules
make demo         # only in repos that have fixtures/invalid/
make rules-table
```

In a repo without these targets, run the steps directly: `ast-grep test`, `ast-grep scan`, `lint-imports` (if `.importlinter` exists), and `mstack coverage`, `mstack exceptions` and `mstack leak-check`.

Commit the YAML, its tests and the `.mdc` together, one commit per rule, with a Conventional Commits message (`feat(rules): add <id> check`).

## Adopting in a repo with no `lint-rules/`

Create the minimal layout before the first check:

```yaml
# lint-rules/sgconfig.yml
ruleDirs:
  - rules
testConfigs:
  - testDir: rule-tests
```

and add `ast-grep-cli` (and `import-linter` for architecture rules) to the repo's dev dependencies. Propose the Makefile targets and CI job from the mstack README; do not add them without approval.

## Personal set

Checks for your own preferences live outside every repo, in `$MY_RULES_HOME` (default `~/.config/my-rules/`). Same recipe, with these differences:

- Ids are prefixed `my-` (`my-no-print`), and the prose rule is `~/.cursor/rules/my-<name>.mdc`, whose Checks section lists the `my-` ids.
- YAML goes to `$MY_RULES_HOME/rules/`, tests to `$MY_RULES_HOME/rule-tests/`. `metadata.source` is the `.mdc` path with `~` (`~/.cursor/rules/my-<name>.mdc`).
- No repo paths at all: no `files` globs naming a repo, no examples from a repo.
- Exceptions are lines in `$MY_RULES_HOME/ignore-paths.txt` (`<glob> [rule-id]`), never `ast-grep-ignore` comments, because nothing is written into other people's repos.
- Only the lint level exists: architecture contracts and tests live in a repo and require changing it.
- Ship personal rules as `error`. `my-rules-check` fails only on errors and nothing passes `--error` to it, so a `warning` in the personal set never blocks anything and the rule becomes advisory. Do not downgrade a rule because of a known glob limitation (for example `files: "**/test_*.py"` also matching files under a folder named `test_*`, since `*` matches `/`): record the limitation in the rule's `note`, and keep test sandboxes out of such folders.
- Test and verify with:

  ```bash
  uv run ast-grep test -c "$MY_RULES_HOME/sgconfig.yml" --skip-snapshot-tests
  mstack coverage --rules-dir ~/.cursor/rules \
    --config "$MY_RULES_HOME/sgconfig.yml" --glob 'my-*.mdc' --root ~ --importlinter /dev/null
  mstack leak-check <generated files> --repo <the repo you were working in>
  ```

- Check a file by hand with `$MY_RULES_HOME/bin/my-rules-check <files>` (add `--with-repo` to also run the current repo's `lint-rules/`).
- Commit in `$MY_RULES_HOME` only if it is a git repo; `ignore-paths.txt` stays in its `.gitignore`.
- The personal set is installed from the mstack checkout with `uv run python scripts/setup.py user` (see the mstack README).
