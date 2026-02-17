---
name: smtp-mail-send
description: Send email via SMTP directly (without Mail.app automation) using environment-provided credentials. Use when Mail.app AppleScript sending is blocked/flaky (for example Apple Events permission errors), or when deterministic programmatic delivery is required with to/cc/bcc/attachments.
---

# SMTP Mail Send

## Overview

Send mail through SMTP with a deterministic Python script.
Use this skill when Mail.app automation is unreliable or blocked.

## Workflow

1. Prepare SMTP environment variables:
- `SMTP_HOST` (required)
- `SMTP_PORT` (optional, default `465`)
- `SMTP_USER` (required)
- `SMTP_PASS` (required)
- `SMTP_STARTTLS` (optional, `1`/`true` to force STARTTLS)

2. Prepare message inputs:
- `--to` required (comma-separated)
- `--cc` / `--bcc` optional
- `--subject` optional
- `--body` or `--body-file`
- `--attach` repeatable absolute file paths

3. Run script:

```bash
python3 /Users/chappie/.codex/skills/smtp-mail-send/scripts/send_smtp_mail.py \
  --to "person@example.com" \
  --subject "Subject" \
  --body "Hello from SMTP"
```

4. If send fails, report the exact SMTP error and whether the failure happened on connect/auth/send.

## Commands

Send with attachment:

```bash
python3 /Users/chappie/.codex/skills/smtp-mail-send/scripts/send_smtp_mail.py \
  --to "person@example.com" \
  --cc "cc@example.com" \
  --subject "Report" \
  --body-file "/tmp/report.txt" \
  --attach "/tmp/report.txt"
```

Force STARTTLS (common on 587):

```bash
SMTP_PORT=587 SMTP_STARTTLS=1 \
python3 /Users/chappie/.codex/skills/smtp-mail-send/scripts/send_smtp_mail.py \
  --to "person@example.com" \
  --subject "STARTTLS test" \
  --body "ok"
```

## Notes

- Keep credentials in environment variables; do not hardcode in commands/files.
- This skill is transport-only and does not manage provider APIs, templates, or tracking.
- If the user explicitly wants Mail.app UI behavior (Drafts/Sent visibility in app), use `macos-mail-send` instead.
