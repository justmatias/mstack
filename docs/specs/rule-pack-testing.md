# Rule pack: tests

- **Phase:** now
- **Depends on:** none

## Problem

There are no rules for test code, the part of a repo agents edit the most. They make the same mistakes there: sleeping instead of waiting for a condition, catching any exception in `pytest.raises`, skipping tests without saying why, testing internals instead of behavior.

## Goal

A `rules/testing.mdc` rule for Python tests (pytest), with checks for what is checkable and `llm-review` for the rest.

## Out of scope

- Coverage thresholds and test runners in CI.
- Other languages' test frameworks. A later pack can follow the same shape.

## Design

`rules/testing.mdc`, `globs: "**/tests/**/*.py, **/test_*.py"`:

| Bullet | Check | Tool |
| --- | --- | --- |
| Don't sleep in tests; wait for a condition, or inject the clock | `no-sleep-in-tests` | ast-grep: `time.sleep($$$)` and `sleep($$$)` imported from `time`, in test files only |
| `pytest.raises` names the exact exception, never `Exception` or `BaseException` | `no-broad-pytest-raises` | ast-grep: `pytest.raises(Exception $$$)` and `pytest.raises(BaseException $$$)` |
| Every skip or xfail says why | `no-skip-without-reason` | ast-grep: `pytest.mark.skip`, `pytest.mark.xfail` and `pytest.skip()` with no `reason=` argument (or no positional reason for `pytest.skip`) |
| One behavior per test, and the name says which (`test_<behavior>_when_<condition>`) | judgment | `llm-review` |
| Test public behavior, not private helpers or internals | judgment | `llm-review` |
| Unit tests don't reach the network or the real clock | judgment | `llm-review` |
| A test that cannot fail is deleted (for example no assertion, or asserting a mock it just configured) | judgment | `llm-review` |

- The checks use `files:` with structural globs (`**/tests/**`, `**/test_*.py`), never project names.
- `no-print-in-app` already exempts `tests/`; nothing changes there.
- Measure existing violations in this repo before picking severities (recipe step 5).

## Changes

- `rules/testing.mdc`.
- `lint/rules/no-sleep-in-tests.yml`, `no-broad-pytest-raises.yml`, `no-skip-without-reason.yml`, with `metadata.source: rules/testing.mdc`.
- `lint/rule-tests/<id>-test.yml`, with near misses: `asyncio.sleep` awaited inside a helper under test, `pytest.raises(ValueError)`, `pytest.mark.skip(reason="...")`, a method named `sleep` on another object.
- `fixtures/valid/tests/test_pricing.py` (valid tests over `fixtures/valid/domain`), and `fixtures/invalid/testing/test_<check>.py`, one per check.
- Make sure pytest never collects the fixtures: `testpaths = ["tests"]` already limits it. Add `norecursedirs = ["fixtures"]` to be explicit.

## Tests

- `ast-grep test` for the three rules.
- `test_every_invalid_fixture_is_caught` and `test_valid_fixtures_have_no_errors` cover the new fixtures.
- `make test` still collects only `tests/`.

## Acceptance criteria

- [ ] `make lint-rules`, `make demo` and `make test` pass.
- [ ] Each check has a fixture the demo catches.
- [ ] `mstack leak-check` passes on the new rule and checks.

## Open questions

- `asyncio.sleep` in async tests: include it in `no-sleep-in-tests`? Recommendation: yes, with the same message, because the same polling advice applies.
