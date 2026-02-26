#!/usr/bin/env bash
set -euo pipefail

PLATFORM="${1:-}"
PROJECT_DIR="${2:-$(pwd)}"
DEVICE_ID="${3:-}"
HX_APP_PATH="${HBUILDERX_APP_PATH:-/Applications/HBuilderX.app}"
ANDROID_ADB_PATH="${ANDROID_ADB_PATH:-}"
HX_CLI_PATH="${HX_CLI_PATH:-${HX_APP_PATH}/Contents/MacOS/cli}"
LSOF_BIN=""

if command -v lsof >/dev/null 2>&1; then
  LSOF_BIN="lsof"
elif [[ -x "/usr/sbin/lsof" ]]; then
  LSOF_BIN="/usr/sbin/lsof"
fi

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
  echo "usage: preflight-autotest.sh <web|weixin|android|ios|ios-simulator|harmony> [project-dir] [device-id]"
  exit 1
fi

case "$PLATFORM" in
  web|h5) PLATFORM="web" ;;
  weixin|mp-weixin) PLATFORM="weixin" ;;
  android|app-android) PLATFORM="android" ;;
  ios|ios-simulator|app-ios-simulator) PLATFORM="ios" ;;
  app-ios)
    echo "BLOCKER: iOS autotest supports simulator only. Use ios or app-ios-simulator."
    exit 3
    ;;
  harmony|app-harmony) PLATFORM="harmony" ;;
  *)
    echo "BLOCKER: unsupported platform: $PLATFORM"
    exit 2
    ;;
esac

cd "$PROJECT_DIR"

if [[ ! -f package.json ]]; then
  echo "BLOCKER: package.json not found in $PROJECT_DIR"
  exit 2
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "BLOCKER: npx is required but not found."
  exit 2
fi

if [[ ! -x "$HX_CLI_PATH" ]]; then
  echo "BLOCKER: HBuilderX CLI not found at $HX_CLI_PATH"
  exit 3
fi

if ! "$HX_CLI_PATH" uniapp.test --help >/dev/null 2>&1; then
  echo "BLOCKER: HBuilderX CLI uniapp.test command is unavailable."
  echo "NEXT: ensure HBuilderX uni-app autotest plugin is installed and enabled."
  exit 3
fi

if [[ "$PLATFORM" == "android" || "$PLATFORM" == "ios" || "$PLATFORM" == "harmony" ]]; then
  TEST_PLUGIN_DIR="${HX_APP_PATH}/Contents/HBuilderX/plugins/hbuilderx-for-uniapp-test"
  TEST_LIB_DIR="${HX_APP_PATH}/Contents/HBuilderX/plugins/hbuilderx-for-uniapp-test-lib/node_modules"
  if [[ ! -d "$TEST_PLUGIN_DIR" ]]; then
    echo "BLOCKER: HBuilderX uni-app autotest plugin directory is missing."
    exit 3
  fi
  if [[ ! -d "$TEST_LIB_DIR" ]]; then
    echo "BLOCKER: uni-app autotest runtime dependencies are missing."
    echo "NEXT: open HBuilderX and reinstall/repair uni-app autotest environment."
    exit 3
  fi
fi

if [[ "$PLATFORM" == "android" ]]; then
  AUTOTEST_ANDROID_PORT="${AUTOTEST_ANDROID_PORT:-9520}"
  AUTOTEST_ANDROID_RUNTIME_PORT=9520
  ADB_BIN=""
  ONLINE_DEVICE_IDS=""
  ONLINE_EMULATOR_IDS=""
  SUGGESTED_DEVICE_ID=""
  if [[ -n "$ANDROID_ADB_PATH" && -x "$ANDROID_ADB_PATH" ]]; then
    ADB_BIN="$ANDROID_ADB_PATH"
  elif command -v adb >/dev/null 2>&1; then
    ADB_BIN="adb"
  elif [[ -x "$HOME/Library/Android/sdk/platform-tools/adb" ]]; then
    ADB_BIN="$HOME/Library/Android/sdk/platform-tools/adb"
  fi

  if [[ -z "$ADB_BIN" ]]; then
    echo "BLOCKER: adb not found. Install Android platform-tools or set ANDROID_ADB_PATH."
    exit 3
  fi

  ADB_DEVICES_OUTPUT="$("$ADB_BIN" devices 2>/dev/null || true)"
  if [[ -z "$ADB_DEVICES_OUTPUT" ]]; then
    echo "BLOCKER: adb is unavailable or no device/emulator is attached."
    echo "NEXT: start an Android emulator or connect a device, then rerun."
    exit 3
  fi

  DEVICE_COUNT="$(printf "%s\n" "$ADB_DEVICES_OUTPUT" | rg -c '\tdevice$' || true)"
  if [[ -z "$DEVICE_COUNT" || "$DEVICE_COUNT" -lt 1 ]]; then
    echo "BLOCKER: no Android device in device state."
    exit 3
  fi

  ONLINE_DEVICE_IDS="$(printf "%s\n" "$ADB_DEVICES_OUTPUT" | tail -n +2 | awk '$2=="device"{print $1}' || true)"
  ONLINE_EMULATOR_IDS="$(printf "%s\n" "$ONLINE_DEVICE_IDS" | rg '^emulator-' || true)"

  if [[ -n "$DEVICE_ID" ]]; then
    if ! printf "%s\n" "$ONLINE_DEVICE_IDS" | grep -Fxq "$DEVICE_ID"; then
      echo "BLOCKER: specified Android device_id not found: $DEVICE_ID"
      echo "NEXT: run adb devices -l and choose an online device id."
      exit 3
    fi
    if ! "$ADB_BIN" -s "$DEVICE_ID" get-state >/dev/null 2>&1; then
      echo "BLOCKER: specified Android device_id is not ready: $DEVICE_ID"
      echo "NEXT: run adb -s $DEVICE_ID get-state and ensure it is 'device'."
      exit 3
    fi
  elif [[ "$DEVICE_COUNT" -gt 1 ]]; then
    SUGGESTED_DEVICE_ID="$(printf "%s\n" "$ONLINE_EMULATOR_IDS" | head -n 1 || true)"
    if [[ -z "$SUGGESTED_DEVICE_ID" ]]; then
      SUGGESTED_DEVICE_ID="$(printf "%s\n" "$ONLINE_DEVICE_IDS" | head -n 1 || true)"
    fi
    if [[ -n "$SUGGESTED_DEVICE_ID" ]]; then
      echo "WARN: multiple Android devices detected; pin device_id to avoid ambiguous target."
      echo "SUGGESTED_DEVICE_ID=$SUGGESTED_DEVICE_ID"
    fi
  fi

  if env | rg -q '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)='; then
    echo "WARN: proxy environment variables detected; runtime socket connection may fail."
  fi

  if [[ "$AUTOTEST_ANDROID_PORT" != "$AUTOTEST_ANDROID_RUNTIME_PORT" ]]; then
    echo "WARN: official HBuilderX CLI runtime port is fixed to ${AUTOTEST_ANDROID_RUNTIME_PORT}; AUTOTEST_ANDROID_PORT=${AUTOTEST_ANDROID_PORT} is diagnostic only."
  fi

  if [[ -n "$LSOF_BIN" ]]; then
    RUNTIME_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_ANDROID_RUNTIME_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    if [[ -n "$RUNTIME_PORT_PIDS" ]]; then
      echo "BLOCKER: Android autotest runtime port ${AUTOTEST_ANDROID_RUNTIME_PORT} is in use (pid): ${RUNTIME_PORT_PIDS}"
      echo "NEXT: ${LSOF_BIN} -nP -tiTCP:${AUTOTEST_ANDROID_RUNTIME_PORT} -sTCP:LISTEN | xargs kill"
      exit 3
    fi

    if [[ "$AUTOTEST_ANDROID_PORT" != "$AUTOTEST_ANDROID_RUNTIME_PORT" ]]; then
      CUSTOM_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_ANDROID_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
      if [[ -n "$CUSTOM_PORT_PIDS" ]]; then
        echo "WARN: custom diagnostic port ${AUTOTEST_ANDROID_PORT} is in use (pid): ${CUSTOM_PORT_PIDS}"
      fi
    fi
  else
    echo "WARN: lsof not found; cannot pre-check Android autotest port."
  fi
fi

if [[ "$PLATFORM" == "ios" ]]; then
  AUTOTEST_IOS_PORT="${AUTOTEST_IOS_PORT:-9520}"
  AUTOTEST_IOS_RUNTIME_PORT=9520
  echo "CHECK: iOS autotest runs on iOS Simulator only."

  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "BLOCKER: iOS automation requires macOS."
    exit 3
  fi

  if ! command -v xcrun >/dev/null 2>&1; then
    echo "BLOCKER: xcrun not found. Install Xcode command line tools."
    exit 3
  fi

  if ! xcrun simctl list runtimes | rg -q "iOS"; then
    echo "BLOCKER: no iOS simulator runtime found."
    exit 3
  fi

  if ! xcrun simctl list devices available | rg -q "iPhone|iPad"; then
    echo "BLOCKER: no available iOS simulator device."
    exit 3
  fi

  if [[ "$AUTOTEST_IOS_PORT" != "$AUTOTEST_IOS_RUNTIME_PORT" ]]; then
    echo "WARN: official HBuilderX CLI runtime port is fixed to ${AUTOTEST_IOS_RUNTIME_PORT}; AUTOTEST_IOS_PORT=${AUTOTEST_IOS_PORT} is diagnostic only."
  fi

  if [[ -n "$LSOF_BIN" ]]; then
    RUNTIME_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_IOS_RUNTIME_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
    if [[ -n "$RUNTIME_PORT_PIDS" ]]; then
      echo "BLOCKER: iOS autotest runtime port ${AUTOTEST_IOS_RUNTIME_PORT} is in use (pid): ${RUNTIME_PORT_PIDS}"
      echo "NEXT: ${LSOF_BIN} -nP -tiTCP:${AUTOTEST_IOS_RUNTIME_PORT} -sTCP:LISTEN | xargs kill"
      exit 3
    fi

    if [[ "$AUTOTEST_IOS_PORT" != "$AUTOTEST_IOS_RUNTIME_PORT" ]]; then
      CUSTOM_PORT_PIDS="$("$LSOF_BIN" -nP -tiTCP:${AUTOTEST_IOS_PORT} -sTCP:LISTEN 2>/dev/null | tr '\n' ' ' | sed 's/[[:space:]]*$//' || true)"
      if [[ -n "$CUSTOM_PORT_PIDS" ]]; then
        echo "WARN: custom diagnostic port ${AUTOTEST_IOS_PORT} is in use (pid): ${CUSTOM_PORT_PIDS}"
      fi
    fi
  else
    echo "WARN: lsof not found; cannot pre-check iOS autotest port."
  fi

  BIN_PATH="${HX_APP_PATH}/Contents/HBuilderX/plugins/uniappx-launcher/base/Pandora_simulator.app/UniAppX"
  if [[ -f "$BIN_PATH" ]] && command -v lipo >/dev/null 2>&1; then
    HOST_ARCH="$(uname -m)"
    BIN_ARCHES="$(lipo -archs "$BIN_PATH" 2>/dev/null || true)"
    if [[ "$HOST_ARCH" == "arm64" ]] && ! printf "%s" "$BIN_ARCHES" | rg -q "arm64"; then
      if printf "%s" "$BIN_ARCHES" | rg -q "x86_64"; then
        RUNTIME_VERBOSE="$(xcrun simctl runtime list -v 2>/dev/null || true)"
        if printf "%s" "$RUNTIME_VERBOSE" | rg -q "Supported Architectures:.*x86_64"; then
          CLI_ARCHES="$(get_binary_arches "$HX_CLI_PATH")"
          if printf "%s" "$CLI_ARCHES" | rg -q "x86_64"; then
            echo "WARN: Pandora_simulator UniAppX is x86_64-only on Apple Silicon."
            echo "WARN: Rosetta x86_64 execution is required for iOS autotest in current setup."
            echo "ROSETTA_REQUIRED=true"
          else
            echo "WARN: launcher is x86_64-only but HBuilderX CLI has no x86_64 slice."
            echo "WARN: skip Rosetta prefix and run CLI with native architecture."
            echo "ROSETTA_REQUIRED=false"
          fi
        else
          echo "BLOCKER: iOS simulator runtime does not expose x86_64 support for current x86_64-only launcher."
          echo "NEXT: install universal iOS runtime (x86_64+arm64) or upgrade launcher to arm64-capable build."
          exit 3
        fi
      else
        echo "BLOCKER: Pandora_simulator UniAppX has no usable architecture for this host."
        echo "NEXT: upgrade HBuilderX/uniappx-launcher."
        exit 3
      fi
    fi
  fi

  if ! pgrep -f "HBuilderX" >/dev/null 2>&1; then
    echo "WARN: HBuilderX process is not running. Start HBuilderX before test execution."
  fi
fi

if [[ "$PLATFORM" == "harmony" ]]; then
  if ! command -v hdc >/dev/null 2>&1; then
    echo "WARN: hdc command not found. Harmony tests may fail without DevEco toolchain."
  fi
fi

echo "Preflight OK for platform: $PLATFORM"
