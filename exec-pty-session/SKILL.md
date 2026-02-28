---
name: exec-pty-session
description: "Handle interactive exec_command sessions that require stdin by starting with tty=true and reusing session_id. Use when you plan to call write_stdin, run interactive tools, or hit \"write_stdin failed: stdin is closed for this session; rerun exec_command with tty=true to keep stdin open\" errors."
---

# Exec Pty Session

## Overview

Keep interactive exec_command runs alive with a TTY-backed session so write_stdin can feed input reliably.

Trigger signature:
- `write_stdin failed: stdin is closed for this session; rerun exec_command with tty=true to keep stdin open`

## Workflow

1. Start the interactive command with exec_command and `tty=true`.
2. Capture the returned `session_id` from exec_command.
3. Use write_stdin with that `session_id` for all subsequent input.
4. If you see `stdin is closed` or `Unknown process id`, restart the command with `tty=true` and retry.
5. Prefer launching REPLs or long-running CLIs (ssh, python, node, npm, pip) with `tty=true` if you might need stdin later.
6. If the session log repeatedly shows `write_stdin failed: stdin is closed`, treat it as a workflow bug and always start the first exec_command with `tty=true`.
7. Avoid starting with commands that exit immediately (e.g., `pwd`, `echo`) when you plan to call write_stdin.
8. If you know you will call `write_stdin` even once, do not "probe" with a non-TTY exec first; open the persistent TTY session as the first command.
9. Do not reuse a `session_id` returned from a non-TTY exec; restart the command as TTY-backed instead of retrying `write_stdin` against the closed session.

## Recovery checklist

- If you plan to call write_stdin, start with `tty=true` on the first exec_command.
- Keep the process alive (use a shell or a long-running command) before sending input.
- Use `{"cmd":"bash","tty":true}` as a safe default opener for interactive sessions.
- On `write_stdin failed: stdin is closed`, re-run the command with `tty=true` and reuse the new `session_id`.
- If the same `write_stdin failed` line appears twice in one task, stop retrying against the old session and restart from a fresh TTY-backed opener immediately.
- If a tool may prompt later (ssh login, REPL, installer, long-running CLI), still start with `tty=true` even if the first step is only launching it.
- If you only need to poll output from a live TTY session, use `write_stdin` on that same `session_id` instead of spawning a separate probe command.

## Examples

Start an interactive command:

```json
{"cmd":"bash","tty":true}
```

Send input:

```json
{"session_id":123,"chars":"ls -la\n"}
```

## Notes

- Avoid commands that exit immediately if you need to keep stdin open.
- For non-interactive commands, keep `tty=false` to avoid unnecessary overhead.
