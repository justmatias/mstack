# Agent instructions

- The rules live in `rules/` (prose, source of truth), and their checks in `lint/`. Read the ones that match the files you touch before writing code.
- Before finishing, run `make lint-rules-changed` and fix every error it reports.
- Write everything in English, and never copy domain or business details into rules, checks or tests.
