---
name: exec-pty-session
description: "Handle interactive exec_command sessions that require stdin by starting with tty=true and reusing session_id. Use when you plan to call write_stdin, run interactive tools, or hit \"write_stdin failed: stdin is closed\" errors."
---

# Exec Pty Session

## Overview

Keep interactive exec_command runs alive with a TTY-backed session so write_stdin can feed input reliably.

## Workflow

1. Start the interactive command with exec_command and `tty=true`.
2. Capture the returned `session_id` from exec_command.
3. Use write_stdin with that `session_id` for all subsequent input.
4. If you see `stdin is closed` or `Unknown process id`, restart the command with `tty=true` and retry.
5. Prefer launching REPLs or long-running CLIs (ssh, python, node, npm, pip) with `tty=true` if you might need stdin later.

## Recovery checklist

- If you plan to call write_stdin, start with `tty=true` on the first exec_command.
- Keep the process alive (use a shell or a long-running command) before sending input.
- On `write_stdin failed: stdin is closed`, re-run the command with `tty=true` and reuse the new `session_id`.

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
