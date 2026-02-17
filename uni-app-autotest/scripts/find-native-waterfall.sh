#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "BLOCKER: project dir not found: $PROJECT_DIR" >&2
  exit 2
fi

echo "PROJECT: $PROJECT_DIR"
echo "NOTE: read-only scan for native-waterfall related files and tests."
echo

if command -v rg >/dev/null 2>&1; then
  echo "FILES (name match):"
  rg --files -g '*native-waterfall*' "$PROJECT_DIR" | sed 's#^#- #'
  echo
  echo "TEST FILES (name/content match):"
  rg --files -g '*native-waterfall*.test.js' "$PROJECT_DIR" | sed 's#^#- #'
  rg -n "native-waterfall|NativeWaterfall" "$PROJECT_DIR" -g '*.test.js' | head -n 200
  echo
  echo "SOURCE HITS (uvue/vue/uts/ts/js/json):"
  rg -n "native-waterfall|NativeWaterfall" "$PROJECT_DIR" -g '*.uvue' -g '*.vue' -g '*.uts' -g '*.ts' -g '*.js' -g '*.json' | head -n 200
else
  echo "WARN: rg not found; fallback to find (limited)."
  find "$PROJECT_DIR" -type f \( -name '*native-waterfall*' -o -name '*.uvue' -o -name '*.vue' -o -name '*.uts' \) | head -n 200 | sed 's#^#- #'
fi
