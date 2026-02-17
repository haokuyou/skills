#!/usr/bin/env python3
import re
import sys
from collections import defaultdict


FILE_RE = re.compile(
    r"(?:file://)?(?P<path>\\[?PackagePath\\]?[^\\s:]+\\.(?:kt|kts|swift|m|mm|java|uts|ts|js|vue|uvue))"
    r"(?::(?P<line>\\d+))?(?::(?P<col>\\d+))?"
)
ERROR_HINT_RE = re.compile(
    r"(error|exception|failed|compile|compilation|unresolved reference|no value passed|build failed|error code|error message)",
    re.IGNORECASE,
)
UNI_HASH_RE = re.compile(r"__UNI__[A-Fa-f0-9]+")


def normalize(text: str) -> str:
    text = UNI_HASH_RE.sub("__UNI__<HEX>", text)
    text = re.sub(r"\\b\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z\\b", "<ISO_TS>", text)
    text = re.sub(r"\\b\\d+\\b", "<NUM>", text)
    return text


def read_input(path: str) -> str:
    if path == "-" or path is None:
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = read_input(path)
    lines = data.splitlines()

    errors = []
    signatures = defaultdict(int)
    modules = defaultdict(int)

    for line in lines:
        if not ERROR_HINT_RE.search(line):
            continue
        file_match = FILE_RE.search(line)
        if file_match:
            file_path = file_match.group("path")
            line_no = file_match.group("line") or "-"
            col_no = file_match.group("col") or "-"
            entry = f"{file_path}:{line_no}:{col_no} | {line.strip()}"
            errors.append(entry)
            sig = normalize(line.strip())
            signatures[sig] += 1
            if "uni_modules" in file_path:
                mod = file_path.split("uni_modules", 1)[1].split("/", 2)[1]
                if mod:
                    modules[mod] += 1
        else:
            lower_line = line.lower()
            if "error code" in lower_line or "error message" in lower_line or "error18" in lower_line:
                errors.append(f"NOFILE:-:- | {line.strip()}")
            sig = normalize(line.strip())
            signatures[sig] += 1

    print("ERRORS")
    if errors:
        for e in errors[:200]:
            print(f"- {e}")
    else:
        print("- (no file/line matches found)")

    print("\nSIGNATURES")
    for sig, count in sorted(signatures.items(), key=lambda kv: kv[1], reverse=True)[:50]:
        print(f"- [{count}] {sig}")

    print("\nSUSPECT MODULES")
    if modules:
        for mod, count in sorted(modules.items(), key=lambda kv: kv[1], reverse=True):
            print(f"- {mod} ({count})")
    else:
        print("- (none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
