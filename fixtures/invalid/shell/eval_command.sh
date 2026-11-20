#!/usr/bin/env bash
set -euo pipefail
command="ls $1"
eval "$command"
