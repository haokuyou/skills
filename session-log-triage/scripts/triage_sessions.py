#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from typing import Dict, List, Any

DEFAULT_KEYWORDS = (
    r"error|failed|exception|traceback|blocked|permission|timeout|osascript|AppleScript|hiservices|sandbox|denied|"
    r"报错|错误|异常|失败|超时|阻塞|权限|拒绝|沙箱|崩溃"
)

PATH_RE = re.compile(r"/(?:[A-Za-z0-9._-]+/)+[A-Za-z0-9._-]+")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b|\b[0-9a-fA-F]{8,}\b")
TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
TIME_RE = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
PID_RE = re.compile(r"\bpid[:= ]\d+\b", re.IGNORECASE)
LINE_RE = re.compile(r"(?::|\bline\s)\d+\b", re.IGNORECASE)
BIG_NUM_RE = re.compile(r"\b\d{4,}\b")
MAX_SAMPLE_LEN = 400


def normalize(text: str) -> str:
    text = TS_RE.sub("<TS>", text)
    text = DATE_RE.sub("<DATE>", text)
    text = TIME_RE.sub("<TIME>", text)
    text = UUID_RE.sub("<UUID>", text)
    text = PATH_RE.sub("<PATH>", text)
    text = PID_RE.sub("pid <PID>", text)
    text = LINE_RE.sub(":<LINE>", text)
    text = HEX_RE.sub("<HEX>", text)
    text = BIG_NUM_RE.sub("<NUM>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_texts(line: str, exclude_types: List[str]) -> List[str]:
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return [line]

    entry_type = obj.get("type")
    if entry_type in exclude_types:
        return []

    payload = obj.get("payload") or {}
    texts: List[str] = []

    if entry_type == "response_item":
        if payload.get("type") != "message":
            return []
        role = payload.get("role")
        if role != "assistant":
            return []
        for item in payload.get("content", []):
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    texts.append(text)
        return texts

    if entry_type == "event_msg":
        for key in ("text", "message"):
            text = payload.get(key)
            if isinstance(text, str):
                texts.append(text)
        return texts

    for key in ("text", "message", "error"):
        text = payload.get(key)
        if isinstance(text, str):
            texts.append(text)
    return texts or [line]


def iter_recent_files(root: str, cutoff_ts: float) -> List[str]:
    files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if st.st_mtime >= cutoff_ts:
                files.append(path)
    return sorted(files)


def triage(
    root: str,
    days: int,
    keywords: str,
    max_classes: int,
    max_samples: int,
    exclude_types: List[str],
) -> Dict[str, Any]:
    cutoff_ts = time.time() - (days * 86400)
    files = iter_recent_files(root, cutoff_ts)
    matcher = re.compile(keywords, re.IGNORECASE)

    clusters: Dict[str, Dict[str, Any]] = {}
    total_matches = 0

    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f, 1):
                    texts = extract_texts(line, exclude_types)
                    if not texts:
                        continue
                    for text in texts:
                        for segment in text.splitlines():
                            segment = segment.strip()
                            if not segment:
                                continue
                            if not matcher.search(segment):
                                continue
                            total_matches += 1
                            norm = normalize(segment)
                            entry = clusters.get(norm)
                            if entry is None:
                                entry = {"signature": norm, "count": 0, "samples": []}
                                clusters[norm] = entry
                            entry["count"] += 1
                            if len(entry["samples"]) < max_samples:
                                sample_text = segment
                                if len(sample_text) > MAX_SAMPLE_LEN:
                                    sample_text = sample_text[:MAX_SAMPLE_LEN] + "..."
                                entry["samples"].append(
                                    {"path": path, "line": idx, "text": sample_text}
                                )
        except OSError:
            continue

    cluster_list = sorted(clusters.values(), key=lambda x: x["count"], reverse=True)
    if max_classes > 0:
        cluster_list = cluster_list[:max_classes]

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "root": root,
        "days": days,
        "files_scanned": len(files),
        "matches": total_matches,
        "clusters": cluster_list,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cluster recent session log failures.")
    parser.add_argument("--root", default=os.path.expanduser("~/.codex/sessions"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--keywords", default=DEFAULT_KEYWORDS)
    parser.add_argument("--max-classes", type=int, default=5)
    parser.add_argument("--max-samples", type=int, default=3)
    parser.add_argument(
        "--exclude-types",
        default="turn_context,session_meta",
        help="Comma-separated event types to skip (match JSON type field)",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    exclude_types = [item.strip() for item in args.exclude_types.split(",") if item.strip()]

    result = triage(
        root=args.root,
        days=args.days,
        keywords=args.keywords,
        max_classes=args.max_classes,
        max_samples=args.max_samples,
        exclude_types=exclude_types,
    )

    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=True, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"root: {result['root']}")
        print(f"days: {result['days']}")
        print(f"files_scanned: {result['files_scanned']}")
        print(f"matches: {result['matches']}")
        for cluster in result["clusters"]:
            print("-")
            print(f"  count: {cluster['count']}")
            print(f"  signature: {cluster['signature']}")
            for sample in cluster["samples"]:
                print(f"  sample: {sample['path']}:{sample['line']} {sample['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
