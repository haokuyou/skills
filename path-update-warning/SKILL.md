---
name: path-update-warning
description: Mitigate "could not update PATH" warnings during exec_command by using absolute tool paths or inline PATH. Use when exec_command output mentions PATH update warnings or commands are missing due to PATH.
---

# PATH Update Warning Mitigation

## Overview

Keep command discovery stable even when PATH updates are blocked.

## Workflow

1. If a PATH update warning appears, resolve tool paths with the script below.
2. Re-run commands using absolute paths, or set PATH inline for the command only.
3. Avoid relying on shell init files for PATH changes in exec_command runs.

## Script: resolve binaries

```bash
/Users/chappie/.codex/skills/path-update-warning/scripts/resolve_bin.sh git python3 rg
```

Example inline PATH usage:

```bash
env PATH="/usr/local/bin:/usr/bin:/bin" /usr/bin/git status
```

## Notes

- Prefer absolute paths once resolved to remove PATH ambiguity.
- If a tool is missing from PATH, ask the user where it is installed.
