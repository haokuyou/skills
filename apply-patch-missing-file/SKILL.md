---
name: apply-patch-missing-file
description: "Diagnose apply_patch verification failures caused by missing target files or wrong working directories, especially `apply_patch verification failed: Failed to read file to update ... (os error 2)`. Use when patching fails before diff application due to path resolution issues, including absolute paths under space-heavy or non-ASCII folders."
---

# Apply Patch Missing File

## Overview

Resolve `apply_patch` path failures deterministically before retrying patch operations.  
Focus on quick checks for absolute/relative path mismatch, wrong `workdir`, and non-existent files.

Trigger signatures:
- `apply_patch verification failed: Failed to read file to update ...: No such file or directory (os error 2)`
- `apply_patch verification failed: Failed to read file to update ...`

## Quick start

1. Check path context before retrying:
   - If the failing path is absolute, compare its repository prefix against the current `workdir` first.
2. Parse and classify the error:
   - `python3 /Users/chappie/.codex/skills/apply-patch-missing-file/scripts/triage_apply_patch_missing_file.py --error "<full apply_patch error>" --workdir "<current workdir>"`
3. Apply the first valid fix:
   - Correct target path.
   - Or correct `workdir`.
   - Or create/move file only if the task clearly requires a new file.
4. Re-run `apply_patch` with the corrected path context.

## Workflow

1. Extract the failed file path from the error text.
2. Preserve the exact path string if it contains spaces or non-ASCII characters; do not hand-trim or retype the failing path before verification.
3. Check whether the path is absolute.
4. If absolute path does not exist, find correct file with `rg --files | rg '<filename>$'`.
5. If relative path was intended, ensure `apply_patch` path is relative to the actual repository root.
6. Verify `workdir` matches the repository where the file exists.
7. If the failing absolute path points into another repo tree, switch `workdir` or patch the real file path instead of retyping the same path.
8. Retry patch only after `test -f` confirms the target file exists.
9. If the same missing-file signature repeats for multiple files in one task, stop retrying patches and re-confirm the repository root once before any further `apply_patch`.

## Decision rules

- Use `*** Add File:` only when user/task explicitly requests creating a new file.
- Use `*** Update File:` only for existing files.
- Do not guess unknown paths; locate exact file first.
- Prefer absolute workspace validation (`pwd`, `ls`) before patch retry.
- Repeated `os error 2` lines in the same task usually mean path context is wrong, not that each file separately disappeared.
- Localized directory names do not break `apply_patch` by themselves; the usual root cause is wrong root or wrong relative path.

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
