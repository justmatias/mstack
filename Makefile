SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: setup lint-rules lint-rules-changed demo rules-table

setup:
	uv sync
	uv run pre-commit install
	scripts/install_skills.sh

lint-rules:
	@echo "lint-rules: not implemented yet (Phase 3)"

lint-rules-changed:
	@echo "lint-rules-changed: not implemented yet (Phase 3)"

demo:
	@echo "demo: not implemented yet (Phase 2)"

rules-table:
	@echo "rules-table: not implemented yet (Phase 3)"
