---
name: project-doc-sync
description: Keep root project documentation synchronized with real implementation during coding work. Use when Codex is asked to modify an existing codebase and should maintain project context by reading root README.md and log.md before editing, creating them if missing, and updating both after meaningful changes while treating source code and tests as the source of truth.
---

# Project Doc Sync

## Purpose

Maintain a lightweight, reliable project memory in root `README.md` and `log.md`.
Use these files to speed up context loading, but never trust them over real project files.

## Workflow

### 1. Resolve project root

Find the project root before any edits.
- Prefer the current repository root (directory containing `.git`).
- If no `.git` exists, use the user-provided working root.

### 2. Ensure root docs exist

In the project root, ensure:
- `README.md`
- `log.md`

If missing, create minimal versions:

```markdown
# README.md
## Project Overview
## Current Features
## Run and Build
## Key Structure
```

```markdown
# log.md
## Change Log
```

### 3. Load context before coding

Before making changes:
- Read root `README.md` and `log.md`.
- Inspect relevant source files, configs, and tests for the task.
- Note any mismatch between docs and code; plan to correct docs after edits.

### 4. Implement changes in code first

Make functional changes in real project files first.
- Do not treat docs as authoritative behavior.
- Validate with available tests, build, or run commands when practical.

### 5. Update docs after each meaningful change

After each completed change set, update both root docs:

Update `README.md` when behavior, usage, setup, or structure changed.
- Keep it concise and user-facing.
- Remove stale statements that no longer match code.
- Prefer stable facts over temporary implementation details.

Update `log.md` by appending one new entry per change set:

```markdown
## YYYY-MM-DD HH:MM
- Summary: <what changed>
- Files: <file1>, <file2>
- Reason: <why this change was made>
- Verification: <tests/build/manual check or "not run">
```

Use local project language style (Chinese/English) for consistency.

### 6. Resolve documentation conflicts correctly

If `README.md` or `log.md` conflicts with code behavior:
- Trust source files, tests, and runtime evidence.
- Fix docs to match reality in the same work pass.
- Call out high-risk mismatches in the final response.

### 7. Completion checklist

Before finishing:
- Root `README.md` exists and reflects current project behavior.
- Root `log.md` exists and includes this work's entries.
- Any doc claim can be traced to real project files.
- Final summary mentions that docs were synchronized.
