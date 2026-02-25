#!/usr/bin/env bash
set -euo pipefail

# Resolve the timeout implementation for scripts that expect timeout/gtimeout.
if command -v gtimeout >/dev/null 2>&1; then
  echo "timeout_cmd=gtimeout"
  echo "timeout_path=$(command -v gtimeout)"
  exit 0
fi

if command -v timeout >/dev/null 2>&1; then
  echo "timeout_cmd=timeout"
  echo "timeout_path=$(command -v timeout)"
  exit 0
fi

echo "timeout_cmd=none"
echo "hint=No timeout/gtimeout found; use script-level watchdog fallback."
