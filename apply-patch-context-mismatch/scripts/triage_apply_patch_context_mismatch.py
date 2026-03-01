#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import Dict, List, Optional


RE_FIND_EXPECTED = re.compile(
    r"Failed to find expected lines in (?P<path>.+?):\s*$"
)
RE_UTF8 = re.compile(
    r"Failed to read(?: file to update)? (?P<path>.+?): stream did not contain valid UTF-8"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Triage apply_patch context mismatch failures."
    )
    parser.add_argument("--error", required=True, help="Full apply_patch error text.")
    parser.add_argument(
        "--workdir",
        default=os.getcwd(),
        help="Current workdir used for apply_patch.",
    )
    parser.add_argument(
        "--needle",
        default="",
        help="Expected anchor line/text in target file (optional).",
    )
    return parser.parse_args()


def detect_signature(error: str) -> Dict[str, Optional[str]]:
    m = RE_FIND_EXPECTED.search(error)
    if m:
        return {"type": "failed_to_find_expected_lines", "path": m.group("path")}

    m = RE_UTF8.search(error)
    if m:
        return {"type": "invalid_utf8_target", "path": m.group("path")}

    return {"type": "unknown", "path": None}


def resolve_target(path: Optional[str], workdir: str) -> Optional[str]:
    if not path:
        return None
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(workdir, path))


def check_utf8(path: str) -> bool:
    with open(path, "rb") as f:
        data = f.read()
    data.decode("utf-8")
    return True


def check_needle(path: str, needle: str) -> int:
    if not needle:
        return -1
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return content.count(needle)


def recommendations(
    signature_type: str,
    target_exists: bool,
    utf8_ok: Optional[bool],
    needle_count: int,
    target_path: Optional[str],
) -> List[str]:
    recs: List[str] = []
    if not target_path:
        recs.append("无法解析目标路径：复制完整 apply_patch 报错后重试。")
        return recs

    if not target_exists:
        recs.append("目标文件不存在：先修正 workdir 或目标路径，再重试 patch。")
        recs.append("执行: rg --files | rg '<文件名>$' 定位真实文件。")
        return recs

    if utf8_ok is False:
        recs.append("目标文件不是有效 UTF-8 文本：不要用 apply_patch 修改该文件。")
        recs.append("若是编译产物或二进制（如 .pyc），改为生成源文件或删除后重建。")
        return recs

    if signature_type == "failed_to_find_expected_lines":
        if needle_count == 0:
            recs.append("锚点文本未找到：当前文件内容已漂移，先读取最新上下文再重建 hunk。")
        elif needle_count > 0:
            recs.append("锚点文本存在：缩小 patch hunk，保留精确缩进与相邻行。")
        else:
            recs.append("未提供 --needle：建议补充期望锚点文本以确认上下文漂移。")
        recs.append("执行: sed -n '1,200p' <目标文件> 后基于当前内容重写最小补丁。")
    elif signature_type == "invalid_utf8_target":
        recs.append("报错指向非 UTF-8 目标：避免继续 patch，转为文本源文件修改流程。")
    else:
        recs.append("签名未识别：先确认是否为 Failed to find expected lines 或 UTF-8 报错。")

    return recs


def main() -> None:
    args = parse_args()
    signature = detect_signature(args.error.strip())
    target_path = resolve_target(signature["path"], os.path.abspath(args.workdir))

    target_exists = False
    utf8_ok: Optional[bool] = None
    needle_count = -1

    if target_path and os.path.exists(target_path):
        target_exists = True
        try:
            utf8_ok = check_utf8(target_path)
        except Exception:
            utf8_ok = False
        if utf8_ok:
            try:
                needle_count = check_needle(target_path, args.needle)
            except Exception:
                needle_count = -1

    result = {
        "signature_type": signature["type"],
        "parsed_target": signature["path"],
        "resolved_target": target_path,
        "target_exists": target_exists,
        "utf8_ok": utf8_ok,
        "needle_count": needle_count,
        "recommendations": recommendations(
            signature["type"], target_exists, utf8_ok, needle_count, target_path
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
