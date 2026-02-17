#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 [--all] '<pattern>'" >&2
  echo "Search the vendored uni-app x docs snapshot under references/upstream/." >&2
  exit 2
fi

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_DIR="$ROOT_DIR/references/upstream/unidocs-uni-app-x-zh"

if [[ ! -d "$UPSTREAM_DIR" ]]; then
  echo "Upstream docs not found at: $UPSTREAM_DIR" >&2
  exit 1
fi

SCOPE_DIRS=("$UPSTREAM_DIR/docs/uts" "$UPSTREAM_DIR/docs/page.md" "$UPSTREAM_DIR/docs/sample.md")

if [[ "${1:-}" == "--all" ]]; then
  shift
  if [[ $# -lt 1 ]]; then
    echo "Usage: $0 [--all] '<pattern>'" >&2
    exit 2
  fi
  SCOPE_DIRS=("$UPSTREAM_DIR/docs" "$UPSTREAM_DIR/README.md")
fi

PATTERN="$1"

if command -v rg >/dev/null 2>&1; then
  rg -n --hidden --no-ignore -S "$PATTERN" "${SCOPE_DIRS[@]}"
else
  grep -RIn -- "$PATTERN" "${SCOPE_DIRS[@]}"
fi
