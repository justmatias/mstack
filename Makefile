SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

AST_GREP := uv run ast-grep
PYTHON := uv run python
SGCONFIG := lint-rules/sgconfig.yml
# fixtures/invalid/ breaks every rule on purpose; it is only scanned by `make demo`.
SCAN_EXCLUDES := --globs '!fixtures/invalid/**'

.PHONY: setup lint-rules lint-rules-changed guards demo rules-table test lint

# Interactive unless SETUP_ARGS has flags, e.g. make setup SETUP_ARGS="--yes" or
# SETUP_ARGS="--with pre-commit --with claude-hook". See: uv run python scripts/setup.py --help
setup:
	uv sync
	uv run python scripts/setup.py $(SETUP_ARGS)
	@echo "skills: in Claude Code or Cursor, ask the agent to follow skills/setup-mstack/SKILL.md"

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
	@files="$$(scripts/git/changed_files.sh $(if $(STAGED),--staged) | grep -v '^fixtures/invalid/' || true)"; \
	if [[ -z "$$files" ]]; then \
		echo "lint-rules-changed: no changed Python files to scan"; \
	else \
		echo "$$files" | xargs $(AST_GREP) scan -c $(SGCONFIG) --error; \
	fi
	@$(MAKE) --no-print-directory guards

guards:
	uv run lint-imports
	$(PYTHON) -m scripts.guards.check_rule_coverage
	$(PYTHON) -m scripts.guards.check_exceptions
	$(PYTHON) -m scripts.guards.check_no_domain_leak lint-rules .cursor/rules --repo . --exclude scripts --exclude tests --exclude fixtures/invalid

# The scan over fixtures/invalid/ MUST fail: it proves the checks still catch real mistakes.
demo:
	@if $(AST_GREP) scan -c $(SGCONFIG) fixtures/invalid; then \
		echo "demo: the scan found no errors in fixtures/invalid/; the checks are broken" >&2; exit 1; \
	else \
		echo "demo: OK, the scan failed on fixtures/invalid/ as expected"; \
	fi

rules-table:
	$(PYTHON) -m scripts.generate.rules_table

test:
	uv run pytest -q
