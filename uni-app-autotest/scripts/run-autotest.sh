#!/usr/bin/env bash
set -euo pipefail

PLATFORM="${1:-}"
CASE_FILE="${2:-}"
PROJECT_DIR="${3:-$(pwd)}"
DEVICE_ID="${4:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HX_APP_PATH="${HBUILDERX_APP_PATH:-/Applications/HBuilderX.app}"
HX_CLI_PATH="${HX_CLI_PATH:-${HX_APP_PATH}/Contents/MacOS/cli}"
AUTOTEST_TIMEOUT_SEC="${AUTOTEST_TIMEOUT_SEC:-900}"
AUTOTEST_MAX_RETRIES="${AUTOTEST_MAX_RETRIES:-1}"
AUTOTEST_LOG_FILE="${AUTOTEST_LOG_FILE:-}"
AUTOTEST_AUTO_RESTORE="${AUTOTEST_AUTO_RESTORE:-1}"
AUTOTEST_STRATEGY="${AUTOTEST_STRATEGY:-auto}"

TIMEOUT_BIN=""
TIMEOUT_FALLBACK_NOTICE_SHOWN="false"
ACTIVE_RUNNER_PID=""
ACTIVE_WATCHDOG_PID=""
if command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_BIN="gtimeout"
elif command -v timeout >/dev/null 2>&1; then
  TIMEOUT_BIN="timeout"
fi

collect_descendant_pids() {
  local parent_pid="$1"
  local child_pids child_pid

  child_pids="$(pgrep -P "$parent_pid" 2>/dev/null || true)"
  for child_pid in $child_pids; do
    printf "%s\n" "$child_pid"
    collect_descendant_pids "$child_pid"
  done
}

terminate_process_tree() {
  local root_pid="$1"
  local sig pid all_pids descendants

  if [[ -z "$root_pid" ]] || ! [[ "$root_pid" =~ ^[0-9]+$ ]]; then
    return 0
  fi

  descendants="$(collect_descendant_pids "$root_pid" 2>/dev/null | sort -u || true)"
  all_pids="$root_pid"
  if [[ -n "$descendants" ]]; then
    all_pids="$all_pids $descendants"
  fi

  for sig in TERM KILL; do
    for pid in $all_pids; do
      if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" >/dev/null 2>&1; then
        kill "-${sig}" "$pid" >/dev/null 2>&1 || true
      fi
    done
    sleep 1
  done
}

run_once_with_watchdog_timeout() {
  local -a cmd=("$@")
  local rc runner_pid watchdog_pid timeout_mark_file
  timeout_mark_file="$(mktemp)"
  rm -f "$timeout_mark_file"

  if [[ -n "$AUTOTEST_LOG_FILE" ]]; then
    ("${cmd[@]}" 2>&1 | tee -a "$AUTOTEST_LOG_FILE") &
  else
    ("${cmd[@]}") &
  fi
  runner_pid=$!
  ACTIVE_RUNNER_PID="$runner_pid"

  (
    sleep "$AUTOTEST_TIMEOUT_SEC"
    if kill -0 "$runner_pid" >/dev/null 2>&1; then
      echo "timeout" > "$timeout_mark_file"
      terminate_process_tree "$runner_pid"
    fi
  ) &
  watchdog_pid=$!
  ACTIVE_WATCHDOG_PID="$watchdog_pid"

  set +e
  wait "$runner_pid"
  rc=$?
  set -e

  kill "$watchdog_pid" >/dev/null 2>&1 || true
  wait "$watchdog_pid" >/dev/null 2>&1 || true
  ACTIVE_WATCHDOG_PID=""
  ACTIVE_RUNNER_PID=""

  if [[ -f "$timeout_mark_file" ]]; then
    rm -f "$timeout_mark_file"
    return 124
  fi

  rm -f "$timeout_mark_file"
  return "$rc"
}

run_once() {
  local -a cmd=("$@")
  local rc

  if [[ -n "$TIMEOUT_BIN" ]]; then
    if [[ -n "$AUTOTEST_LOG_FILE" ]]; then
      "$TIMEOUT_BIN" "$AUTOTEST_TIMEOUT_SEC" "${cmd[@]}" 2>&1 | tee -a "$AUTOTEST_LOG_FILE"
      rc=${PIPESTATUS[0]}
    else
      "$TIMEOUT_BIN" "$AUTOTEST_TIMEOUT_SEC" "${cmd[@]}"
      rc=$?
    fi
  elif [[ "$AUTOTEST_TIMEOUT_SEC" =~ ^[0-9]+$ ]] && [[ "$AUTOTEST_TIMEOUT_SEC" -gt 0 ]]; then
    if [[ "$TIMEOUT_FALLBACK_NOTICE_SHOWN" != "true" ]]; then
      echo "WARN: timeout/gtimeout not found; using built-in watchdog timeout."
      TIMEOUT_FALLBACK_NOTICE_SHOWN="true"
    fi
    run_once_with_watchdog_timeout "${cmd[@]}"
    rc=$?
  else
    if [[ -n "$AUTOTEST_LOG_FILE" ]]; then
      "${cmd[@]}" 2>&1 | tee -a "$AUTOTEST_LOG_FILE"
      rc=${PIPESTATUS[0]}
    else
      "${cmd[@]}"
      rc=$?
    fi
  fi

  return "$rc"
}

run_with_retries() {
  local -a cmd=("$@")
  local max_attempts attempt rc
  max_attempts=$((AUTOTEST_MAX_RETRIES + 1))
  attempt=0
  rc=1

  while (( attempt < max_attempts )); do
    attempt=$((attempt + 1))
    echo "Attempt ${attempt}/${max_attempts}: ${cmd[*]}"
    set +e
    run_once "${cmd[@]}"
    rc=$?
    set -e

    if [[ "$rc" -eq 0 ]]; then
      return 0
    fi

    if [[ "$rc" -eq 124 ]]; then
      echo "BLOCKER: command timed out after ${AUTOTEST_TIMEOUT_SEC}s."
      echo "NEXT: increase AUTOTEST_TIMEOUT_SEC or inspect environment/plugin status."
      return 124
    fi

    if (( attempt < max_attempts )); then
      echo "Retrying due to non-zero exit code: $rc"
    fi
  done

  return "$rc"
}

normalize_case_file() {
  local case_file="$1"
  local project_dir="$2"

  if [[ -z "$case_file" ]]; then
    echo ""
    return 0
  fi

  if [[ "$case_file" == /* ]]; then
    if [[ "$case_file" == "$project_dir/"* ]]; then
      echo "${case_file#"$project_dir/"}"
      return 0
    fi

    echo "BLOCKER: testcase file must be inside project directory for stable CLI invocation."
    return 1
  fi

  echo "$case_file"
}

get_file_mtime() {
  local file_path="$1"
  if stat -f %m "$file_path" >/dev/null 2>&1; then
    stat -f %m "$file_path"
  else
    stat -c %Y "$file_path"
  fi
}

get_latest_report_info() {
  local report_dir="$1"
  if [[ ! -d "$report_dir" ]]; then
    return 1
  fi

  local latest_line
  latest_line="$(
    find "$report_dir" -maxdepth 1 -type f -name '*.json' -print 2>/dev/null | while read -r file; do
      mtime="$(get_file_mtime "$file" 2>/dev/null || true)"
      if [[ -n "$mtime" ]]; then
        printf "%s\t%s\n" "$mtime" "$file"
      fi
    done | sort -nr | head -n 1
  )"

  if [[ -z "$latest_line" ]]; then
    return 1
  fi

  printf "%s\n" "$latest_line"
}

get_binary_arches() {
  local bin_path="$1"
  local arches=""

  if [[ ! -f "$bin_path" ]]; then
    echo ""
    return 0
  fi

  if command -v lipo >/dev/null 2>&1; then
    arches="$(lipo -archs "$bin_path" 2>/dev/null || true)"
  fi

  if [[ -z "$arches" ]] && command -v file >/dev/null 2>&1; then
    arches="$(file "$bin_path" 2>/dev/null | rg -o 'arm64|x86_64' | sort -u | tr '\n' ' ' || true)"
    arches="$(printf "%s" "$arches" | sed 's/[[:space:]]*$//')"
  fi

  echo "$arches"
}

if [[ -z "$PLATFORM" ]]; then
  echo "usage: run-autotest.sh <web|weixin|android|ios|ios-simulator|harmony|aliases> [case-file] [project-dir] [device-id]"
  exit 1
fi

case "$PLATFORM" in
  web|h5) PLATFORM="web" ;;
  weixin|mp-weixin) PLATFORM="weixin" ;;
  android|app-android) PLATFORM="android" ;;
  ios|ios-simulator|app-ios-simulator) PLATFORM="ios" ;;
  app-ios)
    echo "BLOCKER: iOS autotest supports simulator only. Use ios or app-ios-simulator."
    exit 1
    ;;
  harmony|app-harmony) PLATFORM="harmony" ;;
  *)
    echo "unsupported platform: $PLATFORM"
    exit 1
    ;;
esac

cd "$PROJECT_DIR"

if [[ ! -f package.json ]]; then
  echo "package.json not found in project: $PROJECT_DIR"
  exit 1
fi

ENV_JS_PATH="${PROJECT_DIR}/env.js"
JEST_CONFIG_PATH="${PROJECT_DIR}/jest.config.js"
ENV_JS_BACKUP=""
JEST_CONFIG_BACKUP=""

cleanup_restore_configs() {
  local rc="$?"

  if [[ -n "$ACTIVE_WATCHDOG_PID" ]]; then
    kill "$ACTIVE_WATCHDOG_PID" >/dev/null 2>&1 || true
    wait "$ACTIVE_WATCHDOG_PID" >/dev/null 2>&1 || true
    ACTIVE_WATCHDOG_PID=""
  fi
  if [[ -n "$ACTIVE_RUNNER_PID" ]]; then
    terminate_process_tree "$ACTIVE_RUNNER_PID"
    ACTIVE_RUNNER_PID=""
  fi

  if [[ "$AUTOTEST_AUTO_RESTORE" == "1" || "$AUTOTEST_AUTO_RESTORE" == "true" ]]; then
    if [[ -n "$ENV_JS_BACKUP" && -f "$ENV_JS_BACKUP" && -f "$ENV_JS_PATH" ]]; then
      if ! cmp -s "$ENV_JS_BACKUP" "$ENV_JS_PATH"; then
        cp "$ENV_JS_BACKUP" "$ENV_JS_PATH"
        echo "AUTO_RESTORE: restored env.js"
      fi
    fi

    if [[ -n "$JEST_CONFIG_BACKUP" && -f "$JEST_CONFIG_BACKUP" && -f "$JEST_CONFIG_PATH" ]]; then
      if ! cmp -s "$JEST_CONFIG_BACKUP" "$JEST_CONFIG_PATH"; then
        cp "$JEST_CONFIG_BACKUP" "$JEST_CONFIG_PATH"
        echo "AUTO_RESTORE: restored jest.config.js"
      fi
    fi
  fi

  [[ -n "$ENV_JS_BACKUP" ]] && rm -f "$ENV_JS_BACKUP"
  [[ -n "$JEST_CONFIG_BACKUP" ]] && rm -f "$JEST_CONFIG_BACKUP"

  return "$rc"
}

if [[ "$AUTOTEST_AUTO_RESTORE" == "1" || "$AUTOTEST_AUTO_RESTORE" == "true" ]]; then
  if [[ -f "$ENV_JS_PATH" ]]; then
    ENV_JS_BACKUP="$(mktemp)"
    cp "$ENV_JS_PATH" "$ENV_JS_BACKUP"
  fi
  if [[ -f "$JEST_CONFIG_PATH" ]]; then
    JEST_CONFIG_BACKUP="$(mktemp)"
    cp "$JEST_CONFIG_PATH" "$JEST_CONFIG_BACKUP"
  fi
fi

trap cleanup_restore_configs EXIT INT TERM HUP

if [[ -n "$AUTOTEST_LOG_FILE" ]]; then
  : > "$AUTOTEST_LOG_FILE"
fi

PREFLIGHT_RC=0
PREFLIGHT_ROSETTA_REQUIRED="false"
if [[ -x "${SCRIPT_DIR}/preflight-autotest.sh" ]]; then
  set +e
  PREFLIGHT_OUTPUT="$("${SCRIPT_DIR}/preflight-autotest.sh" "$PLATFORM" "$PROJECT_DIR" "$DEVICE_ID" 2>&1)"
  PREFLIGHT_RC=$?
  set -e
  printf "%s\n" "$PREFLIGHT_OUTPUT"
  if printf "%s\n" "$PREFLIGHT_OUTPUT" | rg -q '^ROSETTA_REQUIRED=true$'; then
    PREFLIGHT_ROSETTA_REQUIRED="true"
  fi
fi

if [[ "$PREFLIGHT_RC" -ne 0 ]]; then
  echo "RUN_STATUS=BLOCKED"
  echo "CODE_EDIT_ALLOWED=false"
  if [[ -x "${SCRIPT_DIR}/fallback-autotest.sh" ]]; then
    "${SCRIPT_DIR}/fallback-autotest.sh" "$PLATFORM" "$PROJECT_DIR" "$CASE_FILE" "$DEVICE_ID"
  fi
  exit "$PREFLIGHT_RC"
fi

echo "RUN_STATUS=READY"
echo "CODE_EDIT_ALLOWED=true"

SCRIPT_NAME="test:uniappx:${PLATFORM}"
HAS_SCRIPT="false"

if npm pkg get "scripts.${SCRIPT_NAME}" 2>/dev/null | rg -qv 'null'; then
  HAS_SCRIPT="true"
fi

if [[ "$HAS_SCRIPT" == "true" && -z "$CASE_FILE" && -z "$DEVICE_ID" && ( "$PLATFORM" == "web" || "$PLATFORM" == "weixin" ) ]]; then
  echo "Running npm script: ${SCRIPT_NAME}"
  run_with_retries npm run "$SCRIPT_NAME"
  exit $?
fi

USE_OFFICIAL_CLI="false"
if [[ "$AUTOTEST_STRATEGY" == "official-cli" ]]; then
  USE_OFFICIAL_CLI="true"
elif [[ "$AUTOTEST_STRATEGY" == "auto" ]]; then
  if [[ "$PLATFORM" == "android" || "$PLATFORM" == "ios" || "$PLATFORM" == "harmony" ]]; then
    USE_OFFICIAL_CLI="true"
  fi
fi

EXEC_RC=1
EXEC_KIND="npx-cli"
REPORT_TRACKING_ENABLED="false"
REPORT_DIR=""
REPORT_BEFORE_TS=0
REPORT_BEFORE_FILE=""

if [[ "$USE_OFFICIAL_CLI" == "true" ]]; then
  if [[ ! -x "$HX_CLI_PATH" ]]; then
    echo "BLOCKER: official HBuilderX CLI not found at $HX_CLI_PATH"
    exit 3
  fi

  HX_PLATFORM="$PLATFORM"
  case "$PLATFORM" in
    android) HX_PLATFORM="app-android" ;;
    ios) HX_PLATFORM="app-ios-simulator" ;;
    harmony) HX_PLATFORM="app-harmony" ;;
  esac

  NORMALIZED_CASE_FILE=""
  if [[ -n "$CASE_FILE" ]]; then
    NORMALIZED_CASE_FILE="$(normalize_case_file "$CASE_FILE" "$PROJECT_DIR")" || {
      echo "CODE_EDIT_ALLOWED=false"
      exit 3
    }
  fi

  CMD=("$HX_CLI_PATH" uniapp.test "$HX_PLATFORM" --project "$PROJECT_DIR")
  if [[ -n "$NORMALIZED_CASE_FILE" ]]; then
    CMD+=(--testcaseFile "$NORMALIZED_CASE_FILE")
  fi
  if [[ -n "$DEVICE_ID" ]]; then
    CMD+=(--device_id "$DEVICE_ID")
  fi

  if [[ "$PLATFORM" == "android" && "${AUTOTEST_ANDROID_PORT:-9520}" != "9520" ]]; then
    echo "WARN: official HBuilderX CLI uses fixed runtime port 9520; AUTOTEST_ANDROID_PORT=${AUTOTEST_ANDROID_PORT} is diagnostic only."
  fi
  if [[ "$PLATFORM" == "ios" && "${AUTOTEST_IOS_PORT:-9520}" != "9520" ]]; then
    echo "WARN: official HBuilderX CLI uses fixed runtime port 9520; AUTOTEST_IOS_PORT=${AUTOTEST_IOS_PORT} is diagnostic only."
  fi

  if [[ "$PLATFORM" == "ios" && "$(uname -m)" == "arm64" && "$PREFLIGHT_ROSETTA_REQUIRED" == "true" && -x "$HX_CLI_PATH" ]]; then
    CLI_ARCHES="$(get_binary_arches "$HX_CLI_PATH")"
    if printf "%s" "$CLI_ARCHES" | rg -q "x86_64"; then
      if command -v arch >/dev/null 2>&1; then
        CMD=(arch -x86_64 "${CMD[@]}")
        echo "EXEC_ARCH=x86_64 (Rosetta)"
      else
        echo "WARN: arch command unavailable; Rosetta fallback cannot be applied."
      fi
    else
      echo "WARN: preflight requested Rosetta but CLI has no x86_64 slice; using native CLI arch."
    fi
  fi

  EXEC_KIND="official-cli"

  case "$PLATFORM" in
    android|ios|harmony)
      REPORT_TRACKING_ENABLED="true"
      REPORT_DIR="${HOME}/Library/Application Support/HBuilder X/hbuilderx-for-uniapp-test/$(basename "$PROJECT_DIR")/${PLATFORM}"
      if REPORT_BEFORE_INFO="$(get_latest_report_info "$REPORT_DIR" 2>/dev/null)"; then
        REPORT_BEFORE_TS="${REPORT_BEFORE_INFO%%$'\t'*}"
        REPORT_BEFORE_FILE="${REPORT_BEFORE_INFO#*$'\t'}"
      fi
      ;;
  esac
else
  CMD=(npx hbuilderx-cli uniapp.test --platform "$PLATFORM")
  if [[ -n "$CASE_FILE" ]]; then
    CMD+=(--case "$CASE_FILE")
  fi
  if [[ -n "$DEVICE_ID" ]]; then
    CMD+=(--device-id "$DEVICE_ID")
  fi
fi

echo "EXEC_STRATEGY=$EXEC_KIND"
echo "Running command: ${CMD[*]}"
set +e
run_with_retries "${CMD[@]}"
EXEC_RC=$?
set -e

if [[ "$EXEC_RC" -ne 0 ]]; then
  if [[ -x "${SCRIPT_DIR}/fallback-autotest.sh" ]]; then
    "${SCRIPT_DIR}/fallback-autotest.sh" "$PLATFORM" "$PROJECT_DIR" "$CASE_FILE" "$DEVICE_ID"
  fi
  exit "$EXEC_RC"
fi

if [[ "$REPORT_TRACKING_ENABLED" == "true" ]]; then
  REPORT_AFTER_INFO="$(get_latest_report_info "$REPORT_DIR" 2>/dev/null || true)"
  REPORT_AFTER_TS=0
  REPORT_AFTER_FILE=""
  if [[ -n "$REPORT_AFTER_INFO" ]]; then
    REPORT_AFTER_TS="${REPORT_AFTER_INFO%%$'\t'*}"
    REPORT_AFTER_FILE="${REPORT_AFTER_INFO#*$'\t'}"
  fi

  if [[ "$REPORT_AFTER_TS" -le 0 ]]; then
    echo "BLOCKER: command exited 0 but no JSON report was generated."
    echo "REPORT_DIR=$REPORT_DIR"
    echo "RUN_STATUS=BLOCKED"
    echo "CODE_EDIT_ALLOWED=false"
    if [[ -x "${SCRIPT_DIR}/fallback-autotest.sh" ]]; then
      "${SCRIPT_DIR}/fallback-autotest.sh" "$PLATFORM" "$PROJECT_DIR" "$CASE_FILE" "$DEVICE_ID"
    fi
    exit 4
  fi

  if [[ "$REPORT_AFTER_TS" -lt "$REPORT_BEFORE_TS" ]] || { [[ "$REPORT_AFTER_TS" -eq "$REPORT_BEFORE_TS" ]] && [[ "$REPORT_AFTER_FILE" == "$REPORT_BEFORE_FILE" ]]; }; then
    echo "BLOCKER: command exited 0 but report was not refreshed for this run."
    echo "LATEST_REPORT=$REPORT_AFTER_FILE"
    echo "REPORT_DIR=$REPORT_DIR"
    echo "RUN_STATUS=BLOCKED"
    echo "CODE_EDIT_ALLOWED=false"
    if [[ -x "${SCRIPT_DIR}/fallback-autotest.sh" ]]; then
      "${SCRIPT_DIR}/fallback-autotest.sh" "$PLATFORM" "$PROJECT_DIR" "$CASE_FILE" "$DEVICE_ID"
    fi
    exit 4
  fi

  echo "LATEST_REPORT=$REPORT_AFTER_FILE"
fi
