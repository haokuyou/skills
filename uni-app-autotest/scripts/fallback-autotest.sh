#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "usage: fallback-autotest.sh <platform> <project-dir> [case-file] [device-id]"
  echo "example: fallback-autotest.sh ios /path/to/project pages/foo.test.js"
  exit 0
fi

PLATFORM="${1:-}"
PROJECT_DIR="${2:-$(pwd)}"
CASE_FILE="${3:-}"
DEVICE_ID="${4:-}"
HX_APP_PATH="${HBUILDERX_APP_PATH:-/Applications/HBuilderX.app}"
ANDROID_ADB_PATH="${ANDROID_ADB_PATH:-}"
LSOF_BIN=""
ADB_BIN_FOR_RERUN=""

if command -v lsof >/dev/null 2>&1; then
  LSOF_BIN="lsof"
elif [[ -x "/usr/sbin/lsof" ]]; then
  LSOF_BIN="/usr/sbin/lsof"
fi

echo "FALLBACK: preflight blocked, running non-invasive checks."
echo "FALLBACK_SCOPE: no file writes, no dependency mutation."
echo "RUN_STATUS=BLOCKED"
echo "CODE_EDIT_ALLOWED=false"
echo "ALLOWED_ACTIONS=read-only-diagnostics"

if [[ -z "$PLATFORM" ]]; then
  echo "WARN: missing platform argument."
  exit 0
fi

# Auto-correct a common argument order mistake: platform + case-file + project-dir.
if [[ ! -d "$PROJECT_DIR" && -n "$CASE_FILE" && -d "$CASE_FILE" ]]; then
  echo "WARN: detected swapped arguments, auto-correcting project-dir and case-file."
  TMP_CASE="$PROJECT_DIR"
  PROJECT_DIR="$CASE_FILE"
  CASE_FILE="$TMP_CASE"
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "WARN: project directory not found: $PROJECT_DIR"
  exit 0
fi

if [[ ! -f "$PROJECT_DIR/package.json" ]]; then
  echo "WARN: package.json not found: $PROJECT_DIR/package.json"
else
  if npm pkg get "devDependencies.@dcloudio/hbuilderx-cli" --prefix "$PROJECT_DIR" 2>/dev/null | rg -q "@dcloudio/hbuilderx-cli"; then
    echo "CHECK: @dcloudio/hbuilderx-cli present in devDependencies (optional when using official HBuilderX CLI)."
  else
    echo "CHECK: @dcloudio/hbuilderx-cli missing in devDependencies (optional)."
    echo "NEXT: keep using official HBuilderX CLI; install package only if project scripts require it."
  fi
fi

if [[ "$PLATFORM" == "ios" ]]; then
  AUTOTEST_IOS_PORT="${AUTOTEST_IOS_PORT:-9520}"
  AUTOTEST_IOS_RUNTIME_PORT=9520
  TEST_LIB_DIR="${HX_APP_PATH}/Contents/HBuilderX/plugins/hbuilderx-for-uniapp-test-lib/node_modules"
  if [[ -d "$TEST_LIB_DIR" ]]; then
    echo "CHECK: test-lib dependencies directory exists."
  else
    echo "WARN: test-lib dependencies directory missing: $TEST_LIB_DIR"
    echo "NEXT: in HBuilderX, reinstall/repair uni-app autotest environment dependencies."
  fi

  if [[ "$AUTOTEST_IOS_PORT" != "$AUTOTEST_IOS_RUNTIME_PORT" ]]; then
    echo "WARN: official HBuilderX CLI runtime port is fixed to ${AUTOTEST_IOS_RUNTIME_PORT}; AUTOTEST_IOS_PORT=${AUTOTEST_IOS_PORT} is diagnostic only."
  fi

  if [[ -n "$LSOF_BIN" ]]; then
    RUNTIME_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_IOS_RUNTIME_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    if [[ -n "$RUNTIME_PORT_PIDS" ]]; then
      echo "WARN: iOS autotest runtime port ${AUTOTEST_IOS_RUNTIME_PORT} is in use (pid): ${RUNTIME_PORT_PIDS}"
      echo "NEXT: ${LSOF_BIN} -nP -tiTCP:${AUTOTEST_IOS_RUNTIME_PORT} -sTCP:LISTEN | xargs kill"
    fi

    if [[ "$AUTOTEST_IOS_PORT" != "$AUTOTEST_IOS_RUNTIME_PORT" ]]; then
      CUSTOM_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_IOS_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
      if [[ -n "$CUSTOM_PORT_PIDS" ]]; then
        echo "WARN: custom diagnostic port ${AUTOTEST_IOS_PORT} is in use (pid): ${CUSTOM_PORT_PIDS}"
      fi
    fi
  fi
fi

if [[ "$PLATFORM" == "android" ]]; then
  AUTOTEST_ANDROID_PORT="${AUTOTEST_ANDROID_PORT:-9520}"
  AUTOTEST_ANDROID_RUNTIME_PORT=9520
  ADB_BIN=""
  if [[ -n "$ANDROID_ADB_PATH" && -x "$ANDROID_ADB_PATH" ]]; then
    ADB_BIN="$ANDROID_ADB_PATH"
  elif command -v adb >/dev/null 2>&1; then
    ADB_BIN="adb"
  elif [[ -x "$HOME/Library/Android/sdk/platform-tools/adb" ]]; then
    ADB_BIN="$HOME/Library/Android/sdk/platform-tools/adb"
  fi

  if [[ -n "$ADB_BIN" ]]; then
    if [[ "$ADB_BIN" != "adb" ]]; then
      ADB_BIN_FOR_RERUN="$ADB_BIN"
    fi
    DEV_COUNT="$("$ADB_BIN" devices | rg -c '\tdevice$' || true)"
    echo "CHECK: adb device count=$DEV_COUNT"
    if [[ -n "$DEVICE_ID" ]]; then
      if "$ADB_BIN" devices | tail -n +2 | cut -f1 | grep -Fxq "$DEVICE_ID"; then
        echo "CHECK: requested device_id online: $DEVICE_ID"
      else
        echo "WARN: requested device_id not online: $DEVICE_ID"
      fi
    fi
  else
    echo "WARN: adb not found for runtime diagnostics."
  fi

  if env | rg -q '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)='; then
    echo "WARN: proxy env detected; runtime socket may fail."
  fi

  if [[ "$AUTOTEST_ANDROID_PORT" != "$AUTOTEST_ANDROID_RUNTIME_PORT" ]]; then
    echo "WARN: official HBuilderX CLI runtime port is fixed to ${AUTOTEST_ANDROID_RUNTIME_PORT}; AUTOTEST_ANDROID_PORT=${AUTOTEST_ANDROID_PORT} is diagnostic only."
  fi

  if [[ -n "$LSOF_BIN" ]]; then
    RUNTIME_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_ANDROID_RUNTIME_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    if [[ -n "$RUNTIME_PORT_PIDS" ]]; then
      echo "WARN: Android autotest runtime port ${AUTOTEST_ANDROID_RUNTIME_PORT} is in use (pid): ${RUNTIME_PORT_PIDS}"
      echo "NEXT: ${LSOF_BIN} -nP -tiTCP:${AUTOTEST_ANDROID_RUNTIME_PORT} -sTCP:LISTEN | xargs kill"
    fi

    if [[ "$AUTOTEST_ANDROID_PORT" != "$AUTOTEST_ANDROID_RUNTIME_PORT" ]]; then
      CUSTOM_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_ANDROID_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
      if [[ -n "$CUSTOM_PORT_PIDS" ]]; then
        echo "WARN: custom diagnostic port ${AUTOTEST_ANDROID_PORT} is in use (pid): ${CUSTOM_PORT_PIDS}"
      fi
    fi
  fi
fi

if [[ -n "$CASE_FILE" ]]; then
  CASE_ABS="$CASE_FILE"
  if [[ "$CASE_FILE" != /* ]]; then
    CASE_ABS="$PROJECT_DIR/$CASE_FILE"
  fi

  if [[ -f "$CASE_ABS" ]]; then
    echo "CHECK: case file exists: $CASE_ABS"
    if command -v node >/dev/null 2>&1; then
      if node --check "$CASE_ABS" >/dev/null 2>&1; then
        echo "CHECK: case file syntax OK."
      else
        echo "WARN: case file syntax check failed."
      fi
    fi
  else
    echo "WARN: case file not found: $CASE_ABS"
  fi
fi

RERUN_CMD=()
if [[ "$PLATFORM" == "android" && -n "$ADB_BIN_FOR_RERUN" ]]; then
  RERUN_CMD+=(env "ANDROID_ADB_PATH=$ADB_BIN_FOR_RERUN")
fi
RERUN_CMD+=("$HOME/.codex/skills/uni-app-autotest/scripts/run-autotest.sh" "$PLATFORM")
if [[ -n "$CASE_FILE" ]]; then
  RERUN_CMD+=("$CASE_FILE")
fi
RERUN_CMD+=("$PROJECT_DIR")
if [[ -n "$DEVICE_ID" ]]; then
  RERUN_CMD+=("$DEVICE_ID")
fi

echo "RERUN_CMD:"
printf "  %q" "${RERUN_CMD[@]}"
printf "\n"
echo "RERUN_CMD_PLAIN:"
printf "  "
for arg in "${RERUN_CMD[@]}"; do
  printf "\"%s\" " "$arg"
done
printf "\n"
