#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Not a git repository: $ROOT"
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
ORIGIN_URL=""
DEFAULT_BRANCH=""

if git remote get-url origin >/dev/null 2>&1; then
  ORIGIN_URL="$(git remote get-url origin)"
fi

if git remote show origin >/dev/null 2>&1; then
  DEFAULT_BRANCH="$(git remote show origin | awk -F': ' '/HEAD branch/ {print $2}' | head -n1)"
fi

if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH="$(git symbolic-ref --quiet refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' || true)"
fi

printf "repo_root: %s\n" "$REPO_ROOT"
if [ -n "$ORIGIN_URL" ]; then
  printf "origin: %s\n" "$ORIGIN_URL"
else
  printf "origin: (none)\n"
fi
if [ -n "$DEFAULT_BRANCH" ]; then
  printf "default_branch: %s\n" "$DEFAULT_BRANCH"
else
  printf "default_branch: (unknown)\n"
fi
