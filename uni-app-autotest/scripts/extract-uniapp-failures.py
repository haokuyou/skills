#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Extract failure blocks from uniapp.test logs.")
    parser.add_argument("logfile", help="Path to uniapp.test log file")
    parser.add_argument("--context", type=int, default=8, help="Lines of context before/after match")
    args = parser.parse_args()

    path = Path(args.logfile)
    if not path.exists():
        raise SystemExit(f"log not found: {path}")

    lines = path.read_text(errors="ignore").splitlines()
    patterns = [
        re.compile(r"Test suite failed to run", re.I),
        re.compile(r"Test Suites:\s*\d+ failed", re.I),
        re.compile(r"error:\s*\[Circular \*\d+\]", re.I),
    ]

    last_end = -1
    for idx, line in enumerate(lines):
        if not any(p.search(line) for p in patterns):
            continue
        start = max(0, idx - args.context)
        end = min(len(lines), idx + args.context + 1)
        if start <= last_end:
            continue
        last_end = end - 1
        print("----")
        print(f"match line {idx + 1}: {line}")
        for i in range(start, end):
            print(f"{i + 1:>6} {lines[i]}")

if __name__ == "__main__":
    main()
