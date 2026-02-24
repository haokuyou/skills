#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path

TARGET_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "Cargo.toml",
    "build.gradle",
    "build.gradle.kts",
    "gradle.properties",
    "Info.plist",
    "VERSION",
    "version.txt",
    "manifest.json",
}

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "DerivedData",
    ".venv",
    "venv",
    "__pycache__",
}

VERSION_RE = re.compile(
    r"(\bversion\b\s*[:=]\s*[\"']?)([0-9A-Za-z._+-]+)",
    re.IGNORECASE,
)

ANDROID_VERSION_RE = re.compile(
    r"\bversion(Name|Code)\b\s*[:=]\s*[\"']?([0-9A-Za-z._+-]+)",
    re.IGNORECASE,
)

IOS_VERSION_RE = re.compile(
    r"(CFBundleShortVersionString|CFBundleVersion)",
    re.IGNORECASE,
)


def iter_targets(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for name in filenames:
            if name in TARGET_FILES:
                yield Path(dirpath) / name


def scan_file(path: Path):
    hits = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return hits

    for idx, line in enumerate(text.splitlines(), 1):
        if VERSION_RE.search(line) or ANDROID_VERSION_RE.search(line) or IOS_VERSION_RE.search(line):
            hits.append((idx, line.strip()))
    return hits


def main():
    ap = argparse.ArgumentParser(description="Find version fields in common project files.")
    ap.add_argument("--root", default=".", help="Project root to scan (default: .)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    found = False
    for path in sorted(iter_targets(root)):
        for line_no, line in scan_file(path):
            found = True
            print(f"{path}:{line_no}:{line}")

    if not found:
        print("No version fields found in common files. Check project-specific configs.")


if __name__ == "__main__":
    main()
