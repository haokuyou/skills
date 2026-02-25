---
name: path-update-warning
description: Mitigate exec_command PATH-related command lookup failures, including "could not update PATH" and "timeout/gtimeout not found", by using absolute paths, inline PATH, or deterministic fallback handling. Use when command resolution fails because PATH updates are blocked or expected binaries are missing.
---

# PATH Update Warning Mitigation

## Overview

Keep command discovery stable even when PATH updates are blocked.

## Workflow

1. If a PATH update warning appears, resolve tool paths with the script below.
2. If a script warns `timeout/gtimeout not found`, detect available timeout implementation and switch to watchdog fallback when none exists.
3. Re-run commands using absolute paths, or set PATH inline for the command only.
4. Avoid relying on shell init files for PATH changes in exec_command runs.

## Script: resolve binaries

```bash
/Users/chappie/.codex/skills/path-update-warning/scripts/resolve_bin.sh git python3 rg
```

Detect timeout command:

```bash
/Users/chappie/.codex/skills/path-update-warning/scripts/detect_timeout_cmd.sh
```

Example inline PATH usage:

```bash
env PATH="/usr/local/bin:/usr/bin:/bin" /usr/bin/git status
```

## Notes

- Prefer absolute paths once resolved to remove PATH ambiguity.
- For timeout-dependent scripts, branch by `timeout_cmd` and keep a script-level watchdog fallback.
- If a tool is missing from PATH, ask the user where it is installed.
