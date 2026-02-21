#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path

DEFAULT_EXCLUDE_DIRS = {".git", "node_modules", "dist", "build", ".output", "out"}

# Match postfix non-null assertions like foo!, arr[i]!, or obj?.prop!
NONNULL_RE = re.compile(r"[A-Za-z0-9_\]\)]!(?!=)")


def iter_files(root: Path, exts: set[str], exclude_dirs: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            if name.split(".")[-1] in exts:
                yield Path(dirpath) / name


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan UTS/UVue files for postfix non-null assertions.")
    parser.add_argument("--root", default=".", help="Root directory to scan (default: current directory).")
    parser.add_argument("--ext", default="uts,uvue", help="Comma-separated extensions (default: uts,uvue).")
    parser.add_argument("--max", type=int, default=200, help="Maximum matches to print (default: 200).")
    args = parser.parse_args()

    exts = {e.strip().lstrip(".") for e in args.ext.split(",") if e.strip()}
    root = Path(args.root).resolve()

    printed = 0
    for path in iter_files(root, exts, DEFAULT_EXCLUDE_DIRS):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(text, 1):
            if "!=" in line or "!==" in line:
                # Skip equality comparisons to reduce noise.
                if not NONNULL_RE.search(line.replace("!=", "")):
                    continue
            if NONNULL_RE.search(line):
                print(f"{path}:{idx}: {line.rstrip()}")
                printed += 1
                if printed >= args.max:
                    return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
