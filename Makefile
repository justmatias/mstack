SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
SGCONFIG := lint-rules/sgconfig.yml

.PHONY: setup lint lint-rules lint-rules-changed demo rules-table

setup:
	uv sync
	uv run pre-commit install
	scripts/install_skills.sh

lint:
	uv run pre-commit run --all-files

lint-rules:
	@echo "lint-rules: not implemented yet (Phase 3)"

lint-rules-changed:
	@echo "lint-rules-changed: not implemented yet (Phase 3)"

# The scan over demo/violations/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) demo/violations; then \
		echo "demo: the scan found no errors in demo/violations/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on demo/violations/ as expected"; \
	fi

rules-table:
	@echo "rules-table: not implemented yet (Phase 3)"
