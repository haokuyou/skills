#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile(r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]"),
    re.compile(r"ImportError: No module named ['\"]([^'\"]+)['\"]"),
]


def extract(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        for pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                found.append(match.group(1))
    return sorted(set(found))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract missing Python modules from logs.")
    parser.add_argument("--file", help="Log file to scan; if omitted, read stdin")
    args = parser.parse_args()

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    else:
        content = sys.stdin.read()

    modules = extract(content)
    if not modules:
        print("No missing modules detected.")
        return 1

    print("Missing modules:")
    for name in modules:
        print(f"- {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
