# Shared helpers for the agent hooks. Sourced, not executed.

# Print the edited file path from a hook payload on stdin (Claude Code or Cursor).
hook_file_path() {
  python3 -c '
import json, sys
payload = json.load(sys.stdin)
tool_input = payload.get("tool_input") or {}
if isinstance(tool_input, str):
    try:
        tool_input = json.loads(tool_input)
    except ValueError:
        tool_input = {}
for key in ("file_path", "path", "target_file"):
    value = tool_input.get(key) or payload.get(key)
    if value:
        print(value)
        break
'
}

# With MSTACK_HOOK_DEBUG=1, append the tool name and input keys of a payload
# (stdin) to $MSTACK_HOOK_DEBUG_LOG (default: mstack-hooks.log in the temp dir).
# Use it to see which tools a real agent session sends to the hook.
hook_debug_log() {
  [[ "${MSTACK_HOOK_DEBUG:-}" == "1" ]] || { cat >/dev/null; return 0; }
  python3 -c '
import datetime, json, sys
payload = json.load(sys.stdin)
tool_input = payload.get("tool_input") or {}
if isinstance(tool_input, str):
    try:
        tool_input = json.loads(tool_input)
    except ValueError:
        tool_input = {}
keys = sorted(tool_input) if isinstance(tool_input, dict) else []
print(datetime.datetime.now().isoformat(timespec="seconds"), sys.argv[1],
      "tool=" + str(payload.get("tool_name")), "input_keys=" + ",".join(keys))
' "$1" >> "${MSTACK_HOOK_DEBUG_LOG:-${TMPDIR:-/tmp}/mstack-hooks.log}" 2>/dev/null || true
}

# Run the repo checks on one file. Prints findings; returns non-zero on errors.
scan_file() {
  local repository_root="$1" file="$2"
  local ast_grep="$repository_root/.venv/bin/ast-grep"
  [[ -x "$ast_grep" ]] || ast_grep="uv run --project $repository_root ast-grep"
  (cd "$repository_root" && $ast_grep scan -c lint-rules/sgconfig.yml --color never "$file")
}
