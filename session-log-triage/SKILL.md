---
name: session-log-triage
description: Scan recent Codex session logs (.jsonl) under ~/.codex/sessions, normalize and cluster repeated failure lines, and report top issues with excerpts. Use when triaging recurring errors/timeouts/sandbox/AppleScript failures from the last N days to decide skill updates.
---

# Session Log Triage

## Overview

Identify high-frequency failure patterns and repeated user requests from recent session logs with deterministic clustering and short excerpts.

## Quick Start

Run the triage script and capture JSON for reporting:

```bash
python3 /Users/chappie/.codex/skills/session-log-triage/scripts/triage_sessions.py \
  --root /Users/chappie/.codex/sessions \
  --days 7 \
  --max-classes 5 \
  --max-samples 3 \
  --json
```

Target one failure family with custom keywords:

```bash
python3 /Users/chappie/.codex/skills/session-log-triage/scripts/triage_sessions.py \
  --root /Users/chappie/.codex/sessions \
  --days 7 \
  --keywords "write_stdin failed|Sandbox\\(Denied|could not update PATH|Operation not permitted \\(os error 1\\)" \
  --max-classes 8 \
  --no-user-requests \
  --json
```

## Workflow

1. Run `triage_sessions.py` with a 7-day window (or the requested window).
2. Use `clusters` to pick the top 3-5 repeated failure signatures.
3. Use `user_request_clusters` to capture repeated user asks that should map to stronger trigger phrasing.
4. For each cluster, copy 1-3 sample lines with file path + line number into the report.
5. Map each cluster to existing skills; update or create skills when a gap is confirmed.
6. Ignore duplicated samples from the same path + line and ignore XML-like environment tag lines so the report stays focused on real user asks.

## Script Reference

`triage_sessions.py` options:

- `--root`: sessions directory (default `~/.codex/sessions`)
- `--days`: lookback window in days (default `7`)
- `--keywords`: regex used for failure matching (default covers failed/exception/timeout/sandbox/permission/AppleScript)
- `--max-classes`: number of clusters to return (default `5`)
- `--max-samples`: samples per cluster (default `3`)
- `--max-user-classes`: number of user-request clusters (default `5`)
- `--max-user-samples`: samples per user cluster (default `3`)
- `--min-user-count`: minimum count for user clusters (default `2`)
- `--no-user-requests`: disable user-request clustering
- `--exclude-types`: comma-separated JSON event types to skip (default `turn_context,session_meta,compacted`)
- `--json`: emit JSON for downstream reporting

## Notes

- The script prioritizes `function_call_output` / `custom_tool_call_output` so failures come from tool outputs instead of prompt boilerplate.
- The script normalizes paths, timestamps, UUIDs, hex tokens, PIDs, and large numbers to improve clustering.
- The script deduplicates identical sample excerpts from the same file + line so one retry loop does not waste all sample slots.
- The script skips known workflow scaffolding lines that often dominate reports but are not actionable on their own (for example `RUN_STATUS=BLOCKED`, `FALLBACK: preflight blocked, running non-invasive checks.`, watchdog timeout fallback notices, and timeout mark cleanup lines).
- The script skips XML-like environment wrapper lines in repeated user-request clustering (for example `<current_date>...</current_date>`) so the request list stays actionable.
- The script drops bare `Traceback (most recent call last):` lines so the cluster surface shifts toward the concrete exception line.
- The script skips known noisy lines that look like failures but are usually benign environment chatter (for example Android emulator `FwdLockEngine` and uniapp pass summaries).
- Keep excerpts short; avoid more than 25 lines per cluster in reports.
