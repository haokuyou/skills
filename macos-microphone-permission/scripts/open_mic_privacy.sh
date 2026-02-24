#!/usr/bin/env bash
set -euo pipefail

open "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"

cat <<'MSG'
Opened: System Settings -> Privacy & Security -> Microphone
If the target app is missing, close it, reopen it, then retry.
If the toggle won't stick, run: tccutil reset Microphone <bundle.id>
MSG
