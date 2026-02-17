---
name: session-log-triage
description: Scan recent Codex session logs (.jsonl) under ~/.codex/sessions, normalize and cluster repeated failure lines, and report top issues with excerpts. Use when triaging recurring errors/timeouts/sandbox/AppleScript failures from the last N days to decide skill updates.
---

# Session Log Triage

## Overview

Identify high-frequency failure patterns in recent session logs with deterministic clustering and short excerpts.

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

## Workflow

1. Run `triage_sessions.py` with a 7-day window (or the requested window).
2. Use `clusters` to pick the top 3-5 repeated issues.
3. For each cluster, copy 1-3 sample lines with file path + line number into the report.
4. Map each cluster to existing skills; update or create skills when a gap is confirmed.

## Script Reference

`triage_sessions.py` options:

- `--root`: sessions directory (default `~/.codex/sessions`)
- `--days`: lookback window in days (default `7`)
- `--keywords`: regex used for matching (default covers error/failed/timeout/sandbox/AppleScript)
- `--max-classes`: number of clusters to return (default `5`)
- `--max-samples`: samples per cluster (default `3`)
- `--exclude-types`: comma-separated JSON event types to skip (default `turn_context,session_meta`)
- `--json`: emit JSON for downstream reporting

## Notes

- The script normalizes paths, timestamps, UUIDs, hex tokens, PIDs, and large numbers to improve clustering.
- Keep excerpts short; avoid more than 25 lines per cluster in reports.
