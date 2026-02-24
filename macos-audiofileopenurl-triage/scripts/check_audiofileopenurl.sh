#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <file-or-glob> [more files/globs...]" >&2
  exit 2
fi

has_afinfo=0
if command -v afinfo >/dev/null 2>&1; then
  has_afinfo=1
fi

expand_arg() {
  local arg="$1"
  local matches=()
  if [[ "$arg" == *"*"* || "$arg" == *"?"* || "$arg" == *"["* ]]; then
    while IFS= read -r f; do
      matches+=("$f")
    done < <(compgen -G "$arg" || true)
  fi
  if [[ ${#matches[@]} -gt 0 ]]; then
    printf '%s\n' "${matches[@]}"
  else
    printf '%s\n' "$arg"
  fi
}

while [[ $# -gt 0 ]]; do
  while IFS= read -r target; do
    echo "== $target"
    if [[ ! -e "$target" ]]; then
      echo "NOT_FOUND"
      continue
    fi
    if [[ ! -r "$target" ]]; then
      echo "NOT_READABLE"
      ls -l "$target" || true
      continue
    fi

    stat -f "size=%z bytes mode=%Sp owner=%Su" "$target" 2>/dev/null || true
    file -b "$target" 2>/dev/null || true

    if [[ $has_afinfo -eq 1 ]]; then
      afinfo "$target" 2>&1 | head -n 8
    else
      echo "AFINFO_MISSING: install Xcode command line tools"
    fi
  done < <(expand_arg "$1")
  shift
  echo "---"
done
