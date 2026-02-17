#!/usr/bin/env bash
set -euo pipefail

path="${1:-}"
if [ -z "$path" ]; then
  echo "usage: check_path_access.sh <path>"
  exit 2
fi

echo "path: $path"
if [ -e "$path" ]; then
  echo "exists: yes"
else
  echo "exists: no"
  exit 1
fi

[ -r "$path" ] && echo "readable: yes" || echo "readable: no"
[ -w "$path" ] && echo "writable: yes" || echo "writable: no"
[ -x "$path" ] && echo "executable: yes" || echo "executable: no"

ls -la "$path" 2>/dev/null | head -n 5 || true
