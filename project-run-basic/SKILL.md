---
name: project-run-basic
description: Identify how to run a project locally using common entrypoints (package.json scripts, Makefile targets, poetry, go.mod, docker compose). Use when a user asks to run the project, start dev server, says "run this project", or uses equivalent Chinese requests like "运行项目"/"运行本项目".
---

# Project Run Basic

## Overview

Detect likely run commands from common project files, then run the most appropriate command.

## Quick start

- Detect run hints:
  - `python3 /Users/chappie/.codex/skills/project-run-basic/scripts/detect_run_hints.py --root /path/to/project`

## Workflow

1. Detect entrypoints
   - Run the hint script to see likely commands.
2. Choose the safest default
   - Prefer `dev` or `start` scripts when present.
   - For Makefile, prefer `run` or `start` targets.
3. Run the command and report output
   - If it fails, capture the error and switch to a fallback from the hints.

## Script reference

- `scripts/detect_run_hints.py` prints common run commands based on project files.

## Notes

- If no hints appear, read README.md or project docs for explicit steps.
