#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
shift || true
APPLY_CHANGES="false"
WRITE_SCRIPTS="false"
ALLOW_INIT="false"

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY_CHANGES="true" ;;
    --write-scripts) WRITE_SCRIPTS="true" ;;
    --allow-init) ALLOW_INIT="true" ;;
    *)
      echo "unknown argument: $arg"
      echo "usage: bootstrap-autotest.sh [project-dir] [--apply] [--write-scripts] [--allow-init]"
      exit 1
      ;;
  esac
done

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but not found."
  exit 1
fi

cd "$PROJECT_DIR"

if [[ ! -f package.json ]]; then
  if [[ "$APPLY_CHANGES" == "true" && "$ALLOW_INIT" == "true" ]]; then
    echo "package.json not found. Running npm init -y ..."
    npm init -y >/dev/null
  else
    echo "BLOCKER: package.json not found."
    echo "NEXT: run npm init -y manually, or rerun with --apply --allow-init."
    exit 2
  fi
fi

if npm pkg get "devDependencies.@dcloudio/hbuilderx-cli" 2>/dev/null | rg -q '@dcloudio/hbuilderx-cli'; then
  echo "CHECK: @dcloudio/hbuilderx-cli already present in devDependencies."
else
  if [[ "$APPLY_CHANGES" == "true" ]]; then
    echo "Installing @dcloudio/hbuilderx-cli ..."
    npm install @dcloudio/hbuilderx-cli --save-dev
  else
    echo "CHECK: @dcloudio/hbuilderx-cli is missing."
    echo "NEXT: run npm install @dcloudio/hbuilderx-cli --save-dev (or rerun with --apply)."
  fi
fi

if [[ "$WRITE_SCRIPTS" == "true" ]]; then
  if [[ "$APPLY_CHANGES" != "true" ]]; then
    echo "BLOCKER: --write-scripts requires --apply."
    exit 2
  fi
  echo "Writing recommended npm scripts ..."
  npm pkg set "scripts.test:uniappx:web=npx hbuilderx-cli uniapp.test --platform web"
  npm pkg set "scripts.test:uniappx:weixin=npx hbuilderx-cli uniapp.test --platform weixin"
  npm pkg set "scripts.test:uniappx:android=npx hbuilderx-cli uniapp.test --platform android"
  npm pkg set "scripts.test:uniappx:ios=npx hbuilderx-cli uniapp.test --platform ios"
  npm pkg set "scripts.test:uniappx:harmony=npx hbuilderx-cli uniapp.test --platform harmony"
fi

echo "Bootstrap finished."
echo "Next:"
echo "1) Ensure HBuilderX uni-app autotest plugin is installed and working in HBuilderX."
echo "2) (Optional) Run preflight: ./scripts/preflight-autotest.sh ios"
echo "3) Run tests: ./scripts/run-autotest.sh web"
