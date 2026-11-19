#!/usr/bin/env bash
# Cursor postToolUse hook (matcher Write). Cursor ignores the output of
# afterFileEdit, so this uses postToolUse and returns the findings as
# additional_context, which Cursor injects after the tool result.
set -uo pipefail
repository_root="$(git rev-parse --show-toplevel)"
source "$repository_root/scripts/hooks/lib.sh"

file="$(hook_file_path)"
if [[ "$file" != *.py || ! -f "$file" ]]; then echo '{}'; exit 0; fi
case "$file" in "$repository_root"/fixtures/invalid/*|fixtures/invalid/*) echo '{}'; exit 0 ;; esac

if output="$(scan_file "$repository_root" "$file" 2>&1)"; then
  echo '{}'
else
  python3 -c 'import json, sys; print(json.dumps({"additional_context": sys.argv[1]}))' \
    "lint-rules: $file breaks a team rule (.cursor/rules). Fix it before continuing:
$output"
fi
exit 0
