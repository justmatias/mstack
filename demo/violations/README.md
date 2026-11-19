# Deliberate violations

Every file in this folder breaks one rule from `.cursor/rules/` on purpose. `make demo` scans this folder and **must fail**: it proves the checks still catch the real mistakes.

| File | Rule | Check |
| --- | --- | --- |
| `dataclass_model.py` | `python-models.mdc` | `prefer-pydantic-over-dataclass` |
| `manual_init.py` | `python-models.mdc` | `no-manual-init-boilerplate` |
| `print_debug.py` | `logging.mdc` | `no-print-in-app` |
| `bare_except.py` | `error-handling.mdc` | `no-bare-except` |
| `swallowed_exception.py` | `error-handling.mdc` | `no-swallowed-exception` |
| `requests_client.py` | `http-client.mdc` | `prefer-httpx-over-requests` |
| `domain_imports_infra.py` | `architecture-layers.mdc` | import-linter `domain-is-pure` (only fails once copied into `example_app/domain/`) |

`naming.mdc` is a judgment rule (`enforcement: llm-review`), so it has no demo file.
