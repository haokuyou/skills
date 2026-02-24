---
name: macos-microphone-permission
description: Resolve macOS microphone permission denials for apps or CLI tools. Use when logs include "Microphone permission denied" or audio capture fails due to macOS Privacy & Security microphone restrictions, and you need concrete steps to grant or reset access.
---

# macOS Microphone Permission

## Overview

Restore microphone access on macOS for the failing app or CLI tool. This skill gives a short decision tree, common fixes, and a helper script to open the Mic privacy pane quickly.

## Workflow

1. Identify the failing app or process that needs mic access.
2. Open the Microphone privacy pane and grant access.
3. Restart the app (or the owning process) and retry.
4. If the toggle is stuck or missing, reset TCC permission and re-grant.

## Decision tree

- If the error string is `Microphone permission denied`:
  - Open the Mic privacy pane and toggle access for the app or terminal.
  - Quit and relaunch the app or shell.
  - Retry the capture.
- If the toggle is missing or won’t stay on:
  - Reset the microphone permission for that app with `tccutil`, then re-grant.

## Common fixes

- Open Microphone privacy pane:
  - `bash /Users/chappie/.codex/skills/macos-microphone-permission/scripts/open_mic_privacy.sh`
- Re-grant access:
  - System Settings -> Privacy & Security -> Microphone -> enable the target app (Terminal, iTerm, Python, browser, etc.).
- Reset permission for a specific app (requires bundle id):
  - `tccutil reset Microphone <bundle.id>`

## Notes

- CLI tools inherit permission from the host app (Terminal/iTerm). Grant mic access to that app.
- After changing privacy settings, you often need to quit/relaunch the app to take effect.

## Resources

### scripts/
- `open_mic_privacy.sh`: open the Microphone privacy pane in System Settings.
