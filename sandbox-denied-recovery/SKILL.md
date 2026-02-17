---
name: sandbox-denied-recovery
description: Recover from exec_command Sandbox(Denied) or permission errors by adjusting workdir and paths to allowed roots. Use when exec_command fails with Sandbox(Denied), permission denied, or exit code 126/128 in sandboxed runs.
---

# Sandbox Denied Recovery

## Overview

Quick checks and a small probe script to confirm path access, then rerun commands within allowed roots.

## Workflow

1. Read the denied path from the error message.
2. Re-run the command with `workdir` set to a known workspace root.
3. Probe access with the script below before retrying risky commands.
4. If access is still denied, ask the user for an allowed path or move/copy files into the workspace.
5. When `find` or recursive scans hit macOS protected folders ("Operation not permitted"), use `safe_find.sh` to prune protected paths and retry.

## Script: check path access

Use `scripts/check_path_access.sh` to confirm read/write/execute permissions.

```bash
/Users/chappie/.codex/skills/sandbox-denied-recovery/scripts/check_path_access.sh \
  "/absolute/path/to/check"
```

## Script: safe find

Use `scripts/safe_find.sh` to avoid macOS protected folders when scanning.

```bash
/Users/chappie/.codex/skills/sandbox-denied-recovery/scripts/safe_find.sh \
  "/Users/you/project" "*.log"
```

## Notes

- Do not use `sandbox_permissions` (policy forbids it). Adjust `workdir` and paths instead.
- Prefer narrow, single-purpose commands when retriable access is uncertain.
