#!/usr/bin/env bash
# Rewrite every pinned mstack version in the docs to $NEW_VERSION.
# semantic-release runs this as part of build_command, so the release commit
# carries the new version everywhere it is written down.
set -euo pipefail

new_version="${NEW_VERSION:?NEW_VERSION is not set}"
files=(README.md docs/workflow.md)

sed -E -i \
  -e "s#(rev: v)[0-9]+\.[0-9]+\.[0-9]+#\1${new_version}#g" \
  -e "s#(justmatias/mstack@v)[0-9]+\.[0-9]+\.[0-9]+#\1${new_version}#g" \
  "${files[@]}"
