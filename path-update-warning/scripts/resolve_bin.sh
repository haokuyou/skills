#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: resolve_bin.sh <cmd> [cmd ...]"
  exit 2
fi

for cmd in "$@"; do
  path="$(command -v "$cmd" || true)"
  if [ -n "$path" ]; then
    echo "$cmd: $path"
  else
    echo "$cmd: not found in PATH"
  fi
done
