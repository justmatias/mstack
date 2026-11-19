SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
PYTHON := uv run python
SGCONFIG := lint-rules/sgconfig.yml
# fixtures/invalid/ breaks every rule on purpose; it is only scanned by `make demo`.
SCAN_EXCLUDES := --globs '!fixtures/invalid/**'

.PHONY: setup lint-rules lint-rules-changed guards demo rules-table test lint

setup:
	uv sync
	uv run pre-commit install
	scripts/install_skills.sh

lint:
	uv run pre-commit run --all-files

# The single command. Hooks, pre-commit and CI call this target (or lint-rules-changed) and nothing else.
lint-rules:
	$(AST_GREP) test -c $(SGCONFIG) --skip-snapshot-tests
	$(AST_GREP) scan -c $(SGCONFIG) $(SCAN_EXCLUDES) .
	@$(MAKE) --no-print-directory guards

# Same as lint-rules, but the scan only covers files changed relative to origin/main
# (BASE_REF overrides it; STAGED=1 uses the staged files). On changed files every
# rule fails, warnings included: only new or touched code has to follow new rules.
lint-rules-changed:
	$(AST_GREP) test -c $(SGCONFIG) --skip-snapshot-tests
	@files="$$(scripts/changed_files.sh $(if $(STAGED),--staged) | grep -v '^fixtures/invalid/' || true)"; \
	if [[ -z "$$files" ]]; then \
		echo "lint-rules-changed: no changed Python files to scan"; \
	else \
		echo "$$files" | xargs $(AST_GREP) scan -c $(SGCONFIG) --error; \
	fi
	@$(MAKE) --no-print-directory guards

guards:
	uv run lint-imports
	$(PYTHON) scripts/check_rule_coverage.py
	$(PYTHON) scripts/check_exceptions.py
	$(PYTHON) scripts/check_no_domain_leak.py lint-rules .cursor/rules --repo . --exclude scripts --exclude tests --exclude fixtures/invalid

# The scan over fixtures/invalid/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) fixtures/invalid; then \
		echo "demo: the scan found no errors in fixtures/invalid/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on fixtures/invalid/ as expected"; \
	fi

rules-table:
	$(PYTHON) scripts/rules_table.py

test:
	uv run pytest -q
