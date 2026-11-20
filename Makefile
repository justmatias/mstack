SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
MSTACK := uv run mstack
SGCONFIG := lint/sgconfig.yml
# This repo keeps its prose rules in rules/ and its checks in lint/; the guards default
# to a work repo's .cursor/rules/ and lint-rules/, so the paths are passed explicitly.
RULE_PATHS := --rules-dir rules --config $(SGCONFIG)
# fixtures/invalid/ breaks every rule on purpose; it is only scanned by `make demo`.
SCAN_EXCLUDES := --globs '!fixtures/invalid/**'

.PHONY: setup lint-rules lint-rules-changed guards demo test lint

# Dev dependencies only. To install the skills and rules into your user folders, ask
# Claude Code or Cursor to follow skills/setup-mstack/SKILL.md.
setup:
	uv sync

lint:
	uv run pre-commit run --all-files

# The single command. pre-commit and CI call this target (or lint-rules-changed) and nothing else.
lint-rules:
	$(AST_GREP) test -c $(SGCONFIG) --skip-snapshot-tests
	$(AST_GREP) scan -c $(SGCONFIG) $(SCAN_EXCLUDES) .
	@$(MAKE) --no-print-directory guards

# Same as lint-rules, but the scan only covers files changed relative to origin/main
# (BASE_REF overrides it; STAGED=1 uses the staged files). On changed files every
# rule fails, warnings included: only new or touched code has to follow new rules.
# CI runs it on pull requests with BASE_REF=origin/<base branch>.
lint-rules-changed:
	$(AST_GREP) test -c $(SGCONFIG) --skip-snapshot-tests
	@changed="$$(scripts/git/changed_files.sh $(if $(STAGED),--staged))"; \
	files="$$(grep -v '^fixtures/invalid/' <<< "$$changed" || true)"; \
	if [[ -z "$$files" ]]; then \
		echo "lint-rules-changed: no changed Python files to scan"; \
	else \
		echo "$$files" | xargs $(AST_GREP) scan -c $(SGCONFIG) --error; \
	fi
	@$(MAKE) --no-print-directory guards

guards:
	uv run lint-imports
	$(MSTACK) coverage $(RULE_PATHS)
	$(MSTACK) exceptions
	$(MSTACK) leak-check lint rules --repo . --exclude src --exclude scripts --exclude tests --exclude fixtures/invalid

# The scan over fixtures/invalid/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) fixtures/invalid; then \
		echo "demo: the scan found no errors in fixtures/invalid/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on fixtures/invalid/ as expected"; \
	fi

test:
	uv run pytest -q
