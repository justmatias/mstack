SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
MSTACK := uv run mstack
RULEPACK := uv run rulepack
# The paths come from .rulepack.toml (sgconfig, scan excludes).
SGCONFIG := lint/sgconfig.yml

.PHONY: setup lint-rules lint-rules-changed repo-guards demo test lint

# Dev dependencies only. To install the skills and rules into your user folders, ask
# your agent to set up mstack (.agents/skills/setup-mstack/SKILL.md).
setup:
	uv sync

lint:
	uv run pre-commit run --all-files

# The single command. pre-commit and CI call this target (or lint-rules-changed) and
# nothing else. `rulepack lint` runs the same steps in any repo.
lint-rules:
	$(RULEPACK) lint
	@$(MAKE) --no-print-directory repo-guards

# Same as lint-rules, but the scan only covers files changed relative to origin/main
# (BASE_REF overrides it; STAGED=1 uses the staged files). On changed files every
# rule fails, warnings included: only new or touched code has to follow new rules.
# CI runs it on pull requests with BASE_REF=origin/<base branch>.
lint-rules-changed:
	$(RULEPACK) lint --changed $(if $(BASE_REF),--base-ref $(BASE_REF)) $(if $(STAGED),--staged)
	@$(MAKE) --no-print-directory repo-guards

# Guards rulepack lint does not run: prose rules match their checks (coverage), skills
# are valid, and every check in lint/ has a rule test.
repo-guards:
	$(MSTACK) coverage --rules-dir rules
	$(MSTACK) skills-check skills .agents/skills
	$(MSTACK) rule-tests-check --sgconfig $(SGCONFIG)

# The scan over fixtures/invalid/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) fixtures/invalid; then \
		echo "demo: the scan found no errors in fixtures/invalid/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on fixtures/invalid/ as expected"; \
	fi

test:
	uv run pytest -q
