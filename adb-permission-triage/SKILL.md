---
name: adb-permission-triage
description: Triage adb shell SecurityException/Permission Denial errors (CALL_PHONE, WRITE_SETTINGS, etc.), extract permission names, and apply safe fallbacks. Use when adb or Android shell commands fail with Permission Denial/SecurityException, or logs include android.permission.* or settings provider access errors.
---

# ADB Permission Triage

## Overview

Identify which Android permissions are missing in adb shell output and choose a safe fallback or grant flow without guessing.

## Quick Start

Parse a log file or tool output to extract permission names and hints:

```bash
python3 /Users/chappie/.codex/skills/adb-permission-triage/scripts/adb_permission_hints.py --input /path/to/log.txt
```

Or pipe command output directly:

```bash
some_adb_command 2>&1 | python3 /Users/chappie/.codex/skills/adb-permission-triage/scripts/adb_permission_hints.py
```

## Workflow

1. Capture the failing adb output (or log).
2. Run `adb_permission_hints.py` to extract permission names.
3. Apply the matching fallback:
   - `CALL_PHONE`: Prefer `android.intent.action.DIAL` + UI tap instead of `CALL`. The shell user cannot hold `CALL_PHONE` on most devices.
   - `WRITE_SETTINGS`: Avoid `settings put` from `com.android.shell`. Use keyevents for volume or grant the permission to the target app package instead.
4. Re-run the adb command with the fallback path.

## Common Signatures

Use these as quick pattern matches when logs are noisy:

- `Permission Denial: starting Intent ... requires android.permission.CALL_PHONE`
- `Error while accessing settings provider` + stack frames:
  - `android.os.Parcel.readException`
  - `android.database.DatabaseUtils.readExceptionFromParcel`

## Fallback Notes

- `CALL_PHONE`:
  - Use `adb shell am start -a android.intent.action.DIAL -d tel:...` then tap the call button via `input tap`.
  - Do not use `android.intent.action.CALL` unless the calling app/package has the permission.
- `WRITE_SETTINGS`:
  - Prefer `adb shell input keyevent KEYCODE_VOLUME_UP` loops for volume changes.
  - If an app package needs it, grant via `adb shell pm grant <pkg> android.permission.WRITE_SETTINGS` or appops, depending on device policy.

## Bundled Resources

### scripts/

- `adb_permission_hints.py`: Extract permission names and emit concise fallback suggestions.
