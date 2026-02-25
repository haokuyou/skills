#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

DEFAULT_KEYWORDS = (
    r"failed|exception|traceback|blocked|permission|timeout|timed out|"
    r"error code|error message|\berror:|compile error|build failed|"
    r"Test suite failed to run|Test Suites: \d+ failed|"
    r"osascript|AppleScript|hiservices|sandbox|denied|write_stdin failed|"
    r"报错|异常|超时|阻塞|权限|拒绝|沙箱|崩溃|错误[:：]|失败[:：]"
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
CHUNK_PREFIX_RE = re.compile(
    r"^(Chunk ID:|Wall time:|Process exited with code|Original token count:|Total output lines:|Output:)"
)
SKIP_REQUEST_PREFIXES = (
    "<environment_context>",
    "</environment_context>",
    "<INSTRUCTIONS>",
    "</INSTRUCTIONS>",
    "<skill>",
    "</skill>",
    "<turn_aborted>",
    "</turn_aborted>",
    "# AGENTS.md instructions",
    "### Available skills",
    "### How to use skills",
    "## Skills",
    "A skill is a set of local instructions",
    "description:",
    "name:",
    "<cwd>",
    "</cwd>",
    "<shell>",
    "</shell>",
    "<name>",
    "</name>",
    "<path>",
    "</path>",
    "---",
)
SKIP_REQUEST_CONTAINS = (
    "After deciding to use a skill",
    "How to use a skill (progressive disclosure)",
    "Do not carry skills across turns unless re-mentioned",
    "Use `multi_tool_use.parallel`",
)
BENIGN_FAILURE_PATTERNS = (
    re.compile(r"FwdLockEngine::onInitialize.*failed:errno = 0", re.IGNORECASE),
    re.compile(r"INFO\s*\|\s*Deleting .* failed", re.IGNORECASE),
    re.compile(r"AiAiFed .*Cancelling training failed", re.IGNORECASE),
    re.compile(r"AppOpService: Ignored setUidMode call for runtime permission app op", re.IGNORECASE),
    re.compile(r"\[uniapp\.test\].*运行失败\s*0.*运行异常\s*0", re.IGNORECASE),
)
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


def normalize_request(text: str) -> str:
    text = PATH_RE.sub("<PATH>", text)
    text = UUID_RE.sub("<UUID>", text)
    text = DATE_RE.sub("<DATE>", text)
    text = BIG_NUM_RE.sub("<NUM>", text)
    text = re.sub(r"`[^`]+`", "`<CODE>`", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clip(text: str, max_len: int = MAX_SAMPLE_LEN) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def is_failure_noise(segment: str) -> bool:
    if not segment:
        return True
    if CHUNK_PREFIX_RE.match(segment):
        return True
    if segment.startswith("{\"timestamp\""):
        return True
    if segment.startswith("```"):
        return True
    if segment.startswith("gAAAAA"):
        return True
    if "setTimeout(" in segment:
        return True
    if re.search(r"\bcatch\s*\(\s*error\s*\)", segment):
        return True
    if segment.startswith("echo ") and "RUN_STATUS=" in segment:
        return True
    if segment.startswith("except Exception as "):
        return True
    if segment.startswith("- Reason:"):
        return True
    for pattern in BENIGN_FAILURE_PATTERNS:
        if pattern.search(segment):
            return True
    return False


def extract_function_output_lines(output: Any) -> List[str]:
    if output is None:
        return []
    if isinstance(output, str):
        raw = output
    else:
        raw = json.dumps(output, ensure_ascii=False)
    if "\nOutput:\n" in raw:
        raw = raw.split("\nOutput:\n", 1)[1]
    lines: List[str] = []
    for part in raw.splitlines():
        segment = part.strip()
        if not segment or CHUNK_PREFIX_RE.match(segment):
            continue
        lines.append(segment)
    return lines


def extract_message_text(payload: Dict[str, Any]) -> str:
    parts: List[str] = []
    for item in payload.get("content", []):
        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text)
    return "\n".join(parts).strip()


def first_meaningful_request_line(text: str) -> Optional[str]:
    trivial = {"好的", "继续", "行", "ok", "OK", "收到"}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in trivial:
            continue
        if line == "<image>":
            continue
        if line == "</image>":
            continue
        if line.startswith("The user interrupted the previous turn on purpose"):
            continue
        if line.startswith("- "):
            continue
        if line.startswith("#"):
            continue
        if line == "metadata:":
            continue
        if line.startswith("```"):
            continue
        if re.match(r"^\d+[.)]\s+", line):
            continue
        if any(token in line for token in SKIP_REQUEST_CONTAINS):
            continue
        if any(line.startswith(prefix) for prefix in SKIP_REQUEST_PREFIXES):
            continue
        return line
    return None


def extract_failure_segments(obj: Dict[str, Any], exclude_types: List[str]) -> List[str]:
    entry_type = obj.get("type")
    if entry_type in exclude_types:
        return []

    payload = obj.get("payload") or {}
    segments: List[str] = []

    if entry_type == "response_item":
        payload_type = payload.get("type")
        if payload_type in ("function_call_output", "custom_tool_call_output"):
            segments.extend(extract_function_output_lines(payload.get("output")))
        return segments

    if entry_type == "event_msg":
        payload_type = payload.get("type")
        if payload_type == "token_count":
            return []
        for key in ("error", "message", "text"):
            text = payload.get(key)
            if isinstance(text, str):
                segments.extend([s.strip() for s in text.splitlines() if s.strip()])
        return segments

    for key in ("text", "message", "error"):
        text = payload.get(key)
        if isinstance(text, str):
            segments.extend([s.strip() for s in text.splitlines() if s.strip()])
    return segments


def extract_user_request(obj: Dict[str, Any], exclude_types: List[str]) -> Optional[str]:
    entry_type = obj.get("type")
    if entry_type in exclude_types:
        return None
    if entry_type != "response_item":
        return None

    payload = obj.get("payload") or {}
    if payload.get("type") != "message":
        return None
    if payload.get("role") != "user":
        return None

    full_text = extract_message_text(payload)
    if not full_text:
        return None
    return first_meaningful_request_line(full_text)


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


def cluster_add(
    buckets: Dict[str, Dict[str, Any]],
    signature: str,
    sample_text: str,
    path: str,
    line_no: int,
    max_samples: int,
) -> None:
    entry = buckets.get(signature)
    if entry is None:
        entry = {"signature": signature, "count": 0, "samples": []}
        buckets[signature] = entry
    entry["count"] += 1
    if len(entry["samples"]) < max_samples:
        entry["samples"].append({"path": path, "line": line_no, "text": clip(sample_text)})


def triage(
    root: str,
    days: int,
    keywords: str,
    max_classes: int,
    max_samples: int,
    exclude_types: List[str],
    include_user_requests: bool,
    max_user_classes: int,
    max_user_samples: int,
    min_user_count: int,
) -> Dict[str, Any]:
    cutoff_ts = time.time() - (days * 86400)
    files = iter_recent_files(root, cutoff_ts)
    matcher = re.compile(keywords, re.IGNORECASE)

    failure_clusters: Dict[str, Dict[str, Any]] = {}
    user_clusters: Dict[str, Dict[str, Any]] = {}
    total_matches = 0
    total_user_messages = 0

    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f, 1):
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    for segment in extract_failure_segments(obj, exclude_types):
                        if is_failure_noise(segment):
                            continue
                        if not matcher.search(segment):
                            continue
                        total_matches += 1
                        cluster_add(
                            failure_clusters,
                            normalize(segment),
                            segment,
                            path,
                            idx,
                            max_samples,
                        )

                    if include_user_requests:
                        request_line = extract_user_request(obj, exclude_types)
                        if request_line:
                            total_user_messages += 1
                            cluster_add(
                                user_clusters,
                                normalize_request(request_line),
                                request_line,
                                path,
                                idx,
                                max_user_samples,
                            )
        except OSError:
            continue

    failure_list = sorted(failure_clusters.values(), key=lambda x: x["count"], reverse=True)
    if max_classes > 0:
        failure_list = failure_list[:max_classes]

    user_list = sorted(user_clusters.values(), key=lambda x: x["count"], reverse=True)
    if min_user_count > 1:
        user_list = [item for item in user_list if item["count"] >= min_user_count]
    if max_user_classes > 0:
        user_list = user_list[:max_user_classes]

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "root": root,
        "days": days,
        "files_scanned": len(files),
        "matches": total_matches,
        "clusters": failure_list,
        "user_messages": total_user_messages,
        "user_request_clusters": user_list,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cluster recent session log failures and repeated user requests.")
    parser.add_argument("--root", default=os.path.expanduser("~/.codex/sessions"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--keywords", default=DEFAULT_KEYWORDS)
    parser.add_argument("--max-classes", type=int, default=5)
    parser.add_argument("--max-samples", type=int, default=3)
    parser.add_argument("--max-user-classes", type=int, default=5)
    parser.add_argument("--max-user-samples", type=int, default=3)
    parser.add_argument("--min-user-count", type=int, default=2)
    parser.add_argument(
        "--exclude-types",
        default="turn_context,session_meta,compacted",
        help="Comma-separated event types to skip (match JSON type field)",
    )
    parser.add_argument(
        "--no-user-requests",
        action="store_true",
        help="Disable repeated user request clustering.",
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
        include_user_requests=not args.no_user_requests,
        max_user_classes=args.max_user_classes,
        max_user_samples=args.max_user_samples,
        min_user_count=args.min_user_count,
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

        if result["user_request_clusters"]:
            print("\nuser_request_clusters")
            for cluster in result["user_request_clusters"]:
                print("-")
                print(f"  count: {cluster['count']}")
                print(f"  signature: {cluster['signature']}")
                for sample in cluster["samples"]:
                    print(f"  sample: {sample['path']}:{sample['line']} {sample['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
