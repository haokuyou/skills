#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PERM_RE = re.compile(r"android\.permission\.[A-Z_]+")
DENY_RE = re.compile(r"Permission Denial|SecurityException", re.IGNORECASE)

HINTS = {
    "android.permission.CALL_PHONE": [
        "Use android.intent.action.DIAL instead of CALL, then tap the call button via input tap.",
        "Shell user typically cannot hold CALL_PHONE; grant it only to an app package if needed.",
    ],
    "android.permission.WRITE_SETTINGS": [
        "Avoid 'settings put' from com.android.shell; use volume keyevents for media volume.",
        "If a specific app needs it, grant WRITE_SETTINGS to that app package (device policy permitting).",
    ],
}


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Android permissions from adb output and print fallback hints.")
    parser.add_argument("--input", help="Path to log/output file. If omitted, read stdin.")
    args = parser.parse_args()

    data = read_input(args.input)
    if not data.strip():
        print("No input provided.")
        return 1

    permissions = sorted(set(PERM_RE.findall(data)))
    has_deny = bool(DENY_RE.search(data))

    if not permissions and not has_deny:
        print("No Permission Denial/SecurityException or permission strings detected.")
        return 0

    if permissions:
        print("Detected permissions:")
        for perm in permissions:
            print(f"- {perm}")
    else:
        print("Permission Denial/SecurityException detected, but no explicit permission name found.")

    print("\nSuggested fallbacks:")
    any_hint = False
    for perm in permissions:
        hints = HINTS.get(perm, [])
        if hints:
            any_hint = True
            print(f"\n{perm}")
            for hint in hints:
                print(f"- {hint}")

    if not any_hint:
        print("- Prefer safer intents (DIAL) over CALL and avoid settings writes from shell.")
        print("- If permission must be granted, target the app package (not com.android.shell) when possible.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
