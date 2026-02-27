---
name: apply-patch-missing-file
description: "Diagnose apply_patch verification failures caused by missing target files or wrong working directories, especially `apply_patch verification failed: Failed to read file to update ... (os error 2)`. Use when patching fails before diff application due to path resolution issues."
---

# Apply Patch Missing File

## Overview

Resolve `apply_patch` path failures deterministically before retrying patch operations.  
Focus on quick checks for absolute/relative path mismatch, wrong `workdir`, and non-existent files.

Trigger signatures:
- `apply_patch verification failed: Failed to read file to update ...: No such file or directory (os error 2)`
- `apply_patch verification failed: Failed to read file to update ...`

## Quick start

1. Parse and classify the error:
   - `python3 /Users/chappie/.codex/skills/apply-patch-missing-file/scripts/triage_apply_patch_missing_file.py --error "<full apply_patch error>" --workdir "<current workdir>"`
2. Apply the first valid fix:
   - Correct target path.
   - Or correct `workdir`.
   - Or create/move file only if the task clearly requires a new file.
3. Re-run `apply_patch` with the corrected path context.

## Workflow

1. Extract the failed file path from the error text.
2. Check whether the path is absolute.
3. If absolute path does not exist, find correct file with `rg --files | rg '<filename>$'`.
4. If relative path was intended, ensure `apply_patch` path is relative to the actual repository root.
5. Verify `workdir` matches the repository where the file exists.
6. Retry patch only after `test -f` confirms the target file exists.
7. If the same missing-file signature repeats for multiple files in one task, stop retrying patches and re-confirm the repository root once before any further `apply_patch`.

## Decision rules

- Use `*** Add File:` only when user/task explicitly requests creating a new file.
- Use `*** Update File:` only for existing files.
- Do not guess unknown paths; locate exact file first.
- Prefer absolute workspace validation (`pwd`, `ls`) before patch retry.
- Repeated `os error 2` lines in the same task usually mean path context is wrong, not that each file separately disappeared.

## Example

Error:
- `apply_patch verification failed: Failed to read file to update /Users/chappie/project/src/app.ts: No such file or directory (os error 2)`

Action:
1. Run triage script with `--error` and `--workdir`.
2. Confirm whether `/Users/chappie/project/src/app.ts` exists.
3. If not, locate true file path with `rg --files`.
4. Retry `apply_patch` with corrected file path.

## Resources

### scripts/
- `triage_apply_patch_missing_file.py`: parse apply_patch missing-file errors and output actionable path/workdir checks.
