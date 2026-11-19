#!/usr/bin/env bash
# List the .py files changed relative to the base branch (default origin/main),
# including uncommitted and untracked files. With --staged, list the staged files.
# Only files that still exist are printed, one per line, relative to the repo root.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ "${1:-}" == "--staged" ]]; then
  git diff --cached --name-only --diff-filter=ACMR -- '*.py'
  exit 0
fi

base_ref="${BASE_REF:-origin/main}"
if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
  base_ref="main"
fi

{
  if merge_base="$(git merge-base "$base_ref" HEAD 2>/dev/null)"; then
    git diff --name-only --diff-filter=ACMR "$merge_base" -- '*.py'
  fi
  git ls-files --others --exclude-standard -- '*.py'
} | sort -u | while IFS= read -r file; do
  if [[ -f "$file" ]]; then printf "%s\n" "$file"; fi
done
