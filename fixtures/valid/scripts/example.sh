#!/usr/bin/env bash
# Copy every file given as an argument into the backup folder.
set -euo pipefail

backup_dir="${BACKUP_DIR:-backups}"

if [[ $# -eq 0 ]]; then
  echo "usage: example.sh <file>..." >&2
  exit 1
fi

mkdir -p "$backup_dir"
stamp="$(date +%Y%m%d)"
for file in "$@"; do
  cp -- "$file" "$backup_dir/$(basename "$file").$stamp"
done
