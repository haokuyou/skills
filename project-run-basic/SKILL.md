---
name: project-run-basic
description: Identify how to run a project locally using common entrypoints (package.json scripts, Makefile targets, poetry, go.mod, docker compose). Use when a user asks to run the project, start dev server, says "run this project", or uses equivalent Chinese requests like "运行项目"/"运行本项目". Keep this skill for generic local start requests; if the user explicitly asks for simulator/device test execution, route to the platform-specific test skill instead.
---

# Project Run Basic

## Overview

Detect likely run commands from common project files, then run the most appropriate command.

## Quick start

- Detect run hints:
  - `python3 /Users/chappie/.codex/skills/project-run-basic/scripts/detect_run_hints.py --root /path/to/project`
- Wait for local HTTP service before probing:
  - `bash /Users/chappie/.codex/skills/project-run-basic/scripts/wait_local_http.sh 5173 / 20`

## Workflow

1. Detect entrypoints
   - Run the hint script to see likely commands.
2. Choose the safest default
   - Prefer `dev` or `start` scripts when present.
   - For Makefile, prefer `run` or `start` targets.
3. Normalize terse requests
   - Treat one-line prompts like `运行项目` or `运行本项目` as permission to inspect common entrypoints first instead of asking for more wording.
4. Run the command and report output
   - If it fails, capture the error and switch to a fallback from the hints.
5. Guard against premature curl checks
   - If verification uses `curl http://127.0.0.1:<port>...`, first wait for readiness with `wait_local_http.sh`.
   - If wait times out, report the timeout instead of repeating `curl: (7) Failed to connect`.

## Script reference

- `scripts/detect_run_hints.py` prints common run commands based on project files.
- `scripts/wait_local_http.sh` waits for `127.0.0.1:<port>` HTTP readiness with a timeout and clear exit code.

## Notes

- If no hints appear, read README.md or project docs for explicit steps.
- If the request includes device or simulator wording (for example "安卓模拟器", "iOS 模拟器", or component-specific test runs), do not stop at a generic start command; hand off to the relevant test skill such as `uni-app-autotest`.
- Repeated `curl: (7) Failed to connect to 127.0.0.1 port ...` usually means the service is not ready yet; use the wait script before concluding startup failed.
- If the main problem is generic `curl (7)` connectivity triage (not just project startup), hand off to `curl-connect-code7-triage`.
