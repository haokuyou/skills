#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Send an email via macOS Mail.app (AppleScript).

Defaults to sending immediately. Use --draft to create a draft instead.

Usage:
  send_mail.sh --to "a@b.com" --subject "Hi" --body "Hello"
  send_mail.sh --draft --to "a@b.com" --subject "Hi" --body-file /path/body.txt --attach /path/file.pdf

Options:
  --to        Comma-separated recipients (required)
  --cc        Comma-separated CC recipients
  --bcc       Comma-separated BCC recipients
  --subject   Subject text (optional)
  --body      Body text (plain text)
  --body-file Read body from file (plain text)
  --attach    Attachment path (repeatable; absolute path recommended)
  --send      Send immediately (default)
  --draft     Create draft (no send)
  --visible   Show the draft window (useful for debugging)
  -h, --help  Show help

Environment:
  CODEX_MAIL_TO  Default value for --to (comma-separated).
EOF
}

to=""
cc=""
bcc=""
subject=""
body=""
body_file=""
mode="send"
visible="0"
declare -a attachments=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) to="${2-}"; shift 2 ;;
    --cc) cc="${2-}"; shift 2 ;;
    --bcc) bcc="${2-}"; shift 2 ;;
    --subject) subject="${2-}"; shift 2 ;;
    --body) body="${2-}"; shift 2 ;;
    --body-file) body_file="${2-}"; shift 2 ;;
    --attach) attachments+=("${2-}"); shift 2 ;;
    --send) mode="send"; shift 1 ;;
    --draft) mode="draft"; shift 1 ;;
    --visible) visible="1"; shift 1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$to" ]]; then
  to="${CODEX_MAIL_TO:-}"
fi

if [[ -z "$to" ]]; then
  echo "Missing --to." >&2
  usage >&2
  exit 2
fi

if [[ -n "$body_file" ]]; then
  if [[ ! -f "$body_file" ]]; then
    echo "Body file not found: $body_file" >&2
    exit 2
  fi
  body="$(cat "$body_file")"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCRIPT="$SCRIPT_DIR/send_mail.applescript"

# Avoid "unbound variable" when no attachments were provided under `set -u`.
if [[ ${#attachments[@]} -eq 0 ]]; then
  exec osascript "$ASCRIPT" "$to" "$cc" "$bcc" "$subject" "$body" "$mode" "$visible"
else
  exec osascript "$ASCRIPT" "$to" "$cc" "$bcc" "$subject" "$body" "$mode" "$visible" "${attachments[@]}"
fi
