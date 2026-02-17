---
name: macos-mail-send
description: Send email via macOS Mail.app using AppleScript (osascript). Use when the user wants Codex to compose a draft or send an email from their Mac using the configured Mail.app account, optionally with CC/BCC and file attachments.
---

# macOS Mail Send

## Overview

Compose a message in Mail.app and send it immediately by default, using a deterministic local script. Use draft mode only when requested.

## Workflow

1. Collect inputs
- `to`: one or more recipients (comma-separated)
- `cc` / `bcc`: optional (comma-separated)
- `subject`: required unless the user explicitly wants a blank subject
- `body`: plain text
- `attachments`: optional list of absolute file paths
- `mode`: `send` (default) or `draft`

2. Create send or draft via script
- Use `scripts/send_mail.sh` (it calls `osascript` and drives Mail.app).
  If you want a fixed recipient, set `CODEX_MAIL_TO` and omit `--to`.

3. Report back
- If `send`: tell the user to check Mail.app Sent.
- If `draft`: tell the user to check Mail.app Drafts.

## Commands

Send (default):
```bash
/Users/chappie/.codex/skills/macos-mail-send/scripts/send_mail.sh \
  --to "person@example.com" \
  --subject "Subject" \
  --body "Hello from Codex."
```

Draft:
```bash
/Users/chappie/.codex/skills/macos-mail-send/scripts/send_mail.sh \
  --draft \
  --to "person@example.com" \
  --cc "cc1@example.com,cc2@example.com" \
  --subject "Subject" \
  --body "Hello from Codex." \
  --attach "/absolute/path/to/file.pdf"
```

## Notes / Troubleshooting

- Mail.app must have at least one account configured, otherwise sending will fail.
- The first run will usually trigger a macOS permission prompt (Terminal/osascript controlling Mail). If blocked, enable it in:
  System Settings -> Privacy & Security -> Automation -> allow your terminal app to control Mail.
- If Apple Events permission is denied (for example `Not authorized to send Apple events` / `-1743`), use `smtp-mail-send` as fallback for deterministic delivery:
  `python3 /Users/chappie/.codex/skills/smtp-mail-send/scripts/send_smtp_mail.py ...`
- Body is plain text. If the user needs HTML formatting, treat that as out of scope unless you extend the script.
