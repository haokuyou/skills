#!/usr/bin/env python3
import argparse
import mimetypes
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import List


def parse_csv(value: str) -> List[str]:
    items = []
    for part in value.split(","):
        addr = part.strip()
        if addr:
            items.append(addr)
    return items


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def read_body(args: argparse.Namespace) -> str:
    if args.body_file:
        p = Path(args.body_file)
        if not p.is_file():
            raise ValueError(f"Body file not found: {p}")
        return p.read_text(encoding="utf-8")
    return args.body or ""


def add_attachments(msg: EmailMessage, attachment_paths: List[str]) -> None:
    for raw_path in attachment_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError(f"Attachment not found: {path}")

        content = path.read_bytes()
        guessed_type, _ = mimetypes.guess_type(str(path))
        if guessed_type:
            maintype, subtype = guessed_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=path.name)


def build_message(args: argparse.Namespace, smtp_user: str) -> EmailMessage:
    to_list = parse_csv(args.to)
    if not to_list:
        raise ValueError("Missing --to recipients")

    cc_list = parse_csv(args.cc) if args.cc else []
    bcc_list = parse_csv(args.bcc) if args.bcc else []

    msg = EmailMessage()
    msg["From"] = args.from_addr or smtp_user
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = args.subject or ""
    msg.set_content(read_body(args))

    add_attachments(msg, args.attach)

    recipients = to_list + cc_list + bcc_list
    if not recipients:
        raise ValueError("No recipients resolved from --to/--cc/--bcc")

    msg.__dict__["_codex_recipients"] = recipients
    return msg


def send_via_smtp(
    msg: EmailMessage,
    host: str,
    port: int,
    user: str,
    password: str,
    force_starttls: bool,
) -> None:
    recipients = msg.__dict__.get("_codex_recipients", [])
    if not recipients:
        raise ValueError("Internal error: missing recipients")

    context = ssl.create_default_context()

    if force_starttls:
        with smtplib.SMTP(host=host, port=port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg, from_addr=msg["From"], to_addrs=recipients)
    else:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=30, context=context) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg, from_addr=msg["From"], to_addrs=recipients)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send email via SMTP.")
    parser.add_argument("--to", required=True, help="Comma-separated recipients")
    parser.add_argument("--cc", default="", help="Comma-separated CC recipients")
    parser.add_argument("--bcc", default="", help="Comma-separated BCC recipients")
    parser.add_argument("--from", dest="from_addr", default="", help="Optional from address")
    parser.add_argument("--subject", default="", help="Email subject")
    parser.add_argument("--body", default="", help="Plain text body")
    parser.add_argument("--body-file", default="", help="Read body from UTF-8 text file")
    parser.add_argument("--attach", action="append", default=[], help="Attachment path (repeatable)")
    parser.add_argument("--host", default=os.getenv("SMTP_HOST", ""), help="SMTP host (or SMTP_HOST)")
    parser.add_argument("--port", type=int, default=int(os.getenv("SMTP_PORT", "465")), help="SMTP port (or SMTP_PORT)")
    parser.add_argument("--user", default=os.getenv("SMTP_USER", ""), help="SMTP user (or SMTP_USER)")
    parser.add_argument("--pass", dest="password", default=os.getenv("SMTP_PASS", ""), help="SMTP password (or SMTP_PASS)")
    parser.add_argument(
        "--starttls",
        action="store_true",
        default=env_bool("SMTP_STARTTLS", False),
        help="Use STARTTLS (or SMTP_STARTTLS=1)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    missing = []
    if not args.host:
        missing.append("SMTP_HOST/--host")
    if not args.user:
        missing.append("SMTP_USER/--user")
    if not args.password:
        missing.append("SMTP_PASS/--pass")

    if missing:
        print("Missing required SMTP configuration: " + ", ".join(missing), file=sys.stderr)
        return 2

    try:
        msg = build_message(args, smtp_user=args.user)
    except Exception as exc:  # pragma: no cover
        print(f"Message build error: {exc}", file=sys.stderr)
        return 2

    try:
        send_via_smtp(
            msg=msg,
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            force_starttls=args.starttls,
        )
    except smtplib.SMTPAuthenticationError as exc:
        print(f"SMTP auth failed: {exc}", file=sys.stderr)
        return 1
    except smtplib.SMTPException as exc:
        print(f"SMTP send failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"SMTP connection failed: {exc}", file=sys.stderr)
        return 1

    print("SMTP send OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
