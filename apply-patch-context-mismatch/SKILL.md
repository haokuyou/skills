---
name: apply-patch-context-mismatch
description: "Diagnose apply_patch verification failures caused by context drift or non-text targets, especially `Failed to find expected lines in ...` and `stream did not contain valid UTF-8`. Use when retries keep failing on the same file because patch anchors no longer match, line endings changed, or a binary/compiled artifact was targeted."
---

# Apply Patch Context Mismatch

## Overview

Resolve `apply_patch` failures where file exists but patch context does not match.
Use a deterministic preflight script before retrying patch generation.

Trigger signatures:
- `apply_patch verification failed: Failed to find expected lines in ...:`
- `apply_patch verification failed: Failed to read ...: stream did not contain valid UTF-8`

## Quick Start

1. Run preflight with the raw error line:
   - `python3 /Users/chappie/.codex/skills/apply-patch-context-mismatch/scripts/triage_apply_patch_context_mismatch.py --error "<full apply_patch error>" --workdir "<current workdir>"`
2. If you know the intended anchor text, add `--needle "<expected line>"` to confirm whether it still exists.
3. Apply the first recommended fix from the script:
   - switch target file if wrong;
   - refresh patch context from current file content;
   - avoid patching binary/compiled artifacts.
4. Retry `apply_patch` only after the script shows `target_exists=true` and no `non_utf8_target` blocker.

## Workflow

1. Parse the failure signature and extract target file path.
2. Confirm file existence under the active `workdir`.
3. Check text readability:
   - If UTF-8 decode fails, treat target as binary/non-text and stop patch retries.
4. For `Failed to find expected lines`:
   - re-open the file;
   - copy current exact context (including indentation and line endings);
   - regenerate minimal patch hunks instead of replaying stale hunks.
5. If retries still fail on the same file, stop and capture one fresh context block with `sed -n` before retrying.

## Decision Rules

- `missing_target`: file path is wrong or workdir is wrong; do not tweak patch text yet.
- `non_utf8_target`: do not use `apply_patch` on `.pyc`, media, or other binary files.
- `needle_not_found`: patch context is stale; re-read file and rebuild hunk.
- `needle_found`: patch likely failed due to indentation or nearby context drift; use a smaller, tighter hunk.

## Example

Error:
- `apply_patch verification failed: Failed to find expected lines in /path/styles.css:`

Action:
1. Run triage script with `--error` and current `--workdir`.
2. Re-open `styles.css`, copy fresh nearby lines, and regenerate minimal hunk.
3. Retry once; if same signature repeats, stop and verify wrong file/path assumptions.

## Resources

### scripts/
- `triage_apply_patch_context_mismatch.py`: parse the error and emit deterministic checks plus next-step commands.
