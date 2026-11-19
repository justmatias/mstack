#!/usr/bin/env bash
# Cursor postToolUse hook, installed with no matcher: Cursor does not document
# which tools edit files, so it runs after every tool and acts only when the tool
# input names an existing .py file. Cursor ignores the output of afterFileEdit,
# so this uses postToolUse and returns the findings as additional_context, which
# Cursor injects after the tool result. MSTACK_HOOK_DEBUG=1 logs every call.
set -uo pipefail
repository_root="$(git rev-parse --show-toplevel)"
source "$repository_root/scripts/hooks/lib.sh"

payload="$(cat)"
printf '%s' "$payload" | hook_debug_log cursor_after_edit
file="$(printf '%s' "$payload" | hook_file_path 2>/dev/null)"
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
