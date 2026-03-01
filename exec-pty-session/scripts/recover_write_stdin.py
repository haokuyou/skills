#!/usr/bin/env python3
import argparse
import json
import re

SIG = re.compile(r"write_stdin failed: stdin is closed for this session", re.IGNORECASE)
UNK = re.compile(r"Unknown process id", re.IGNORECASE)


def main() -> int:
    p = argparse.ArgumentParser(description="Recover plan for write_stdin closed-session failures.")
    p.add_argument("--error", required=True, help="Tool error text from write_stdin")
    p.add_argument("--cmd", default="bash", help="Command to open as TTY session")
    args = p.parse_args()

    error = args.error.strip()
    matched = bool(SIG.search(error) or UNK.search(error))

    result = {
        "matched": matched,
        "restart_required": matched,
        "recommended_exec_command": {"cmd": args.cmd, "tty": True},
        "steps": [
            "使用 exec_command 重新启动 TTY 会话（tty=true）。",
            "记录新的 session_id，并仅对该 session_id 调用 write_stdin。",
            "不要继续对旧 session_id 重试 write_stdin。",
        ],
    }

    if not matched:
        result["steps"] = [
            "错误不匹配 stdin closed/Unknown process id，先按原错误排查。"
        ]

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
