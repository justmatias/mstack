#!/usr/bin/env bash
# Claude Code PostToolUse hook (matcher Edit|Write|MultiEdit). On rule errors in the edited
# .py file, prints them to stderr and exits 2 so Claude sees and fixes them.
set -uo pipefail
repository_root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
source "$repository_root/scripts/hooks/lib.sh"

file="$(hook_file_path)"
[[ "$file" == *.py && -f "$file" ]] || exit 0
case "$file" in "$repository_root"/fixtures/invalid/*|fixtures/invalid/*) exit 0 ;; esac

if ! output="$(scan_file "$repository_root" "$file" 2>&1)"; then
  printf 'lint-rules: %s breaks a team rule (.cursor/rules). Fix it before continuing:\n%s\n' "$file" "$output" >&2
  exit 2
fi
exit 0
