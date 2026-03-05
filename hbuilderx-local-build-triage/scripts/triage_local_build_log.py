#!/usr/bin/env python3
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RULES = [
    (
        "HBX_SWIFT_PARSER_ENOENT",
        re.compile(r"spawnSync\s+.+swift-parser-cli\s+ENOENT", re.IGNORECASE),
        "检查 HBuilderX 安装与 uts-development-ios 插件目录；确认 swift-parser-cli 存在且可执行，必要时重装或升级 HBuilderX。",
    ),
    (
        "UVUE_FONT_WEIGHT_UNSUPPORTED",
        re.compile(
            r"plugin:uni:app-uvue-css.*property value [`'\"]?\d+[`'\"]? is not supported for [`'\"]?font-weight",
            re.IGNORECASE,
        ),
        "将数值 font-weight 调整为平台支持值（优先 normal），避免在 uvue 样式中使用不支持的权重常量。",
    ),
    (
        "PLUGINHOST_CIRCULAR_ERROR",
        re.compile(r"error:\s*\[Circular \*\d+\]", re.IGNORECASE),
        "该行通常是伴随错误；回溯同时间窗口首条真实编译错误，不要把 Circular 行作为根因。",
    ),
]


def read_lines(path: str):
    if path == "-":
        return [line.rstrip("\n") for line in sys.stdin]
    p = Path(path)
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        return [line.rstrip("\n") for line in f]


def extract_text(raw_line: str) -> str:
    """Prefer human-readable payload fields when line is JSONL."""
    line = raw_line.strip()
    try:
        obj = json.loads(line)
        payload = obj.get("payload")
        if isinstance(payload, dict):
            for key in ("output", "text", "stderr", "stdout", "message"):
                val = payload.get(key)
                if isinstance(val, str) and val.strip():
                    return " ".join(val.split())
    except Exception:
        pass
    return " ".join(line.split())


def main():
    parser = argparse.ArgumentParser(
        description="Normalize HBuilderX local build log errors into actionable clusters."
    )
    parser.add_argument("log", help="log file path or '-' for stdin")
    parser.add_argument("--max-samples", type=int, default=3)
    args = parser.parse_args()

    lines = read_lines(args.log)
    hits = defaultdict(list)

    for idx, raw_line in enumerate(lines, 1):
        line = extract_text(raw_line)
        for key, pat, _ in RULES:
            if pat.search(line):
                hits[key].append((idx, line.strip()))

    print("LOCAL_BUILD_TRIAGE")
    print(f"TOTAL_LINES={len(lines)}")
    if not hits:
        print("MATCHED=0")
        print("NO_KNOWN_SIGNATURES=1")
        return

    total = sum(len(v) for v in hits.values())
    print(f"MATCHED={total}")

    sorted_keys = sorted(hits.keys(), key=lambda k: len(hits[k]), reverse=True)
    for key in sorted_keys:
        advice = next(rule[2] for rule in RULES if rule[0] == key)
        print("\n---")
        print(f"SIGNATURE={key}")
        print(f"COUNT={len(hits[key])}")
        for ln, text in hits[key][: max(args.max_samples, 1)]:
            print(f"SAMPLE_LINE={ln}")
            print(f"SAMPLE_TEXT={text[:260]}")
        print(f"ACTION={advice}")


if __name__ == "__main__":
    main()
