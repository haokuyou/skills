---
name: macos-accessibility-permission
description: "Resolve macOS Accessibility permission denials for apps, helpers, or CLI-driven workflows. Use when an app says it needs 辅助功能权限/无障碍权限, when the Privacy & Security Accessibility setting is missing or disabled, or when automation features such as paste, UI control, or accessibility APIs fail until Accessibility permission is granted."
---

# macOS Accessibility Permission

## Overview

Restore Accessibility access on macOS for the app that is blocked. Use a short decision tree, a helper script that opens the Accessibility privacy pane, and only reset TCC when the normal toggle path does not work.

## Workflow

1. Identify the blocked app or host process.
2. Open the Accessibility privacy pane.
3. Enable the app under Accessibility, then quit and relaunch it.
4. If the toggle is missing or stuck, remove and re-add the app, or reset the TCC entry and retry.

## Decision tree

- If the app shows text like `需要辅助功能权限`, `无障碍权限`, or says paste/UI automation requires System Settings approval:
- If the app shows text like `需要辅助功能权限`, `无障碍权限`, `SmartAccess 使用辅助功能权限来提供以下无障碍功能：`, or `本应用需要辅助功能权限才能正常使用粘贴功能`:
  - Open the Accessibility pane with the helper script.
  - Turn on the target app (Terminal, iTerm, Hammerspoon, the app itself, etc.).
  - Quit and relaunch the app, then retry the action.
- If the target app is not listed:
  - Use the `+` button in Accessibility settings to add the app.
  - Reopen the app after it appears in the list.
- If the toggle is listed but turns itself off or the feature still fails:
  - Remove the app from the list and add it again.
  - If needed, reset the Accessibility permission with `tccutil`, then re-grant.
- If the failure is for a CLI tool launched from Terminal/iTerm:
  - Grant Accessibility to the host terminal app, not only the child process.

## Common fixes

- Open the Accessibility privacy pane:
  - `bash /Users/chappie/.codex/skills/macos-accessibility-permission/scripts/open_accessibility_privacy.sh`
- Re-grant access:
  - System Settings -> Privacy & Security -> Accessibility -> enable the target app.
- Reset a stuck permission entry (requires bundle id):
  - `tccutil reset Accessibility <bundle.id>`

## Notes

- Accessibility permission changes usually require quitting and relaunching the affected app.
- CLI automation inherits permissions from the host app, so fix Terminal/iTerm first when shell commands drive UI automation.
- Repeated in-app warnings about 辅助功能权限 are usually configuration problems, not code bugs.
- If the same in-app warning repeats in one session, stop retrying the feature and confirm the host app is actually enabled in System Settings before changing code.

## Resources

### scripts/
- `open_accessibility_privacy.sh`: open the Accessibility privacy pane in System Settings.
