#!/usr/bin/env bash
# List the .py and .sh files changed relative to the base branch (default origin/main),
# including uncommitted and untracked files. With --staged, list the staged files.
# Only files that still exist are printed, one per line, relative to the repo root.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ "${1:-}" == "--staged" ]]; then
  git diff --cached --name-only --diff-filter=ACMR -- '*.py' '*.sh'
  exit 0
fi

# An explicit BASE_REF (as in CI) must exist: falling back would silently scan
# nothing. Only the default falls back to the local main when there is no remote.
if [[ -n "${BASE_REF:-}" ]]; then
  base_ref="$BASE_REF"
  if ! git rev-parse --verify --quiet "$base_ref^{commit}" >/dev/null; then
    echo "changed_files.sh: BASE_REF '$base_ref' does not exist. Fetch it first (CI: actions/checkout with fetch-depth: 0)." >&2
    exit 1
  fi
else
  base_ref="origin/main"
  if ! git rev-parse --verify --quiet "$base_ref^{commit}" >/dev/null; then
    base_ref="main"
  fi
fi

{
  if merge_base="$(git merge-base "$base_ref" HEAD 2>/dev/null)"; then
    git diff --name-only --diff-filter=ACMR "$merge_base" -- '*.py' '*.sh'
  elif [[ -n "${BASE_REF:-}" ]]; then
    echo "changed_files.sh: no merge base between '$base_ref' and HEAD (shallow clone?)." >&2
    exit 1
  fi
  git ls-files --others --exclude-standard -- '*.py' '*.sh'
} | sort -u | while IFS= read -r file; do
  if [[ -f "$file" ]]; then printf "%s\n" "$file"; fi
done
