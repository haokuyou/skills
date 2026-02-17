#!/usr/bin/env bash
set -euo pipefail

root="${1:-}"
pattern="${2:-*}"

if [ -z "$root" ]; then
  echo "usage: safe_find.sh <root> [name-pattern]"
  exit 2
fi

# Avoid macOS protected directories and common heavy folders.
find "$root" \
  -path "$root/.git" -prune -o \
  -path "$root/node_modules" -prune -o \
  -path "$root/Library" -prune -o \
  -path "/Users/*/Library" -prune -o \
  -path "/Users/*/Library/*" -prune -o \
  -name "$pattern" -print 2>/dev/null
