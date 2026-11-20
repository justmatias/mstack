SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
MSTACK := uv run mstack
# The paths (sgconfig, rules, scan excludes) come from .mstack.toml.
SGCONFIG := lint/sgconfig.yml
# The installable files in agents/, mcp/, settings/ and instructions/. Each folder's
# README.md documents the format for this repo and is not installed, so it is left out.
AGENT_CONFIG_FILES := $(filter-out %/README.md,$(wildcard agents/*.md mcp/*.json settings/*.json instructions/*.md))

.PHONY: setup lint-rules lint-rules-changed guards repo-guards demo test lint

# Dev dependencies only. To install the skills and rules into your user folders, run
# /setup-mstack in Claude Code or Cursor.
setup:
	uv sync

lint:
	uv run pre-commit run --all-files

# The single command. pre-commit and CI call this target (or lint-rules-changed) and
# nothing else. `mstack lint` runs the same steps in any repo.
lint-rules:
	$(MSTACK) lint
	@$(MAKE) --no-print-directory repo-guards

# Same as lint-rules, but the scan only covers files changed relative to origin/main
# (BASE_REF overrides it; STAGED=1 uses the staged files). On changed files every
# rule fails, warnings included: only new or touched code has to follow new rules.
# CI runs it on pull requests with BASE_REF=origin/<base branch>.
lint-rules-changed:
	$(MSTACK) lint --changed $(if $(BASE_REF),--base-ref $(BASE_REF)) $(if $(STAGED),--staged)
	@$(MAKE) --no-print-directory repo-guards

guards:
	$(MSTACK) lint --only imports coverage exceptions leak-check
	@$(MAKE) --no-print-directory repo-guards

# Guards for what only this repo has: agent config folders and skills.
repo-guards:
	$(MSTACK) config-check
	$(MSTACK) skills-check skills .claude/skills
	$(if $(AGENT_CONFIG_FILES),$(MSTACK) leak-check $(AGENT_CONFIG_FILES))

# The scan over fixtures/invalid/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) fixtures/invalid; then \
		echo "demo: the scan found no errors in fixtures/invalid/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on fixtures/invalid/ as expected"; \
	fi

test:
	uv run pytest -q
