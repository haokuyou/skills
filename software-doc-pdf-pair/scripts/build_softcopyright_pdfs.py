#!/usr/bin/env python3
"""
Generate software copyright PDFs by cloning template PDFs and patching key fields.
This keeps layout, images, and most content close to the reference documents.
"""

from __future__ import annotations

import argparse
import getpass
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover - runtime dependency check
    print(
        "Missing dependency. Install with: python3 -m pip install pymupdf",
        file=sys.stderr,
    )
    print(f"Import error: {exc}", file=sys.stderr)
    sys.exit(1)


SOURCE_PAGE_COUNT = 70
DESIGN_PAGE_COUNT = 52

REFERENCE_SOFTWARE_NAME = "摊友圈"

FONT_ATTEMPTS = [("china-s", None), ("china-t", None), ("helv", None), ("cour", None)]


@dataclass
class DocConfig:
    software_name: str
    company_name: str
    software_description: str
    version: str
    author: str
    doc_date: str
    output_dir: Path
    template_source: Path
    template_design: Path


def normalize_filename(raw: str) -> str:
    name = raw.strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return name or "软件"


def require_value(value: str | None, prompt: str) -> str:
    if value and value.strip():
        return value.strip()
    entered = input(prompt).strip()
    if not entered:
        raise ValueError(f"Missing required input: {prompt}")
    return entered


def parse_args() -> argparse.Namespace:
    here = Path(__file__).resolve()
    skill_dir = here.parent.parent
    assets = skill_dir / "assets"

    parser = argparse.ArgumentParser(
        description="Generate software copyright PDFs from reference templates."
    )
    parser.add_argument("--software-name")
    parser.add_argument("--company-name")
    parser.add_argument("--software-description")
    parser.add_argument("--version", default="1.0")
    parser.add_argument("--author", default=getpass.getuser())
    parser.add_argument("--doc-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default=str(Path.cwd()))
    parser.add_argument(
        "--template-source",
        default=str(assets / "template-source-list.pdf"),
    )
    parser.add_argument(
        "--template-design",
        default=str(assets / "template-design-spec.pdf"),
    )
    return parser.parse_args()


def draw_boxed_text(page: fitz.Page, rect: fitz.Rect, text: str, align: int = 0) -> None:
    box = fitz.Rect(rect.x0 - 1.0, rect.y0 - 0.8, rect.x1 + 1.0, rect.y1 + 0.8)
    try:
        page.add_redact_annot(box, fill=(1, 1, 1))
        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=0,
            text=0,
        )
    except Exception:
        page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

    page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
    base_size = max(8.0, min(13.0, rect.height * 0.9))

    for font_name, font_file in FONT_ATTEMPTS:
        size = base_size
        while size >= 6.0:
            page.draw_rect(box, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
            try:
                remaining = page.insert_textbox(
                    box,
                    text,
                    fontsize=size,
                    fontname=font_name,
                    fontfile=font_file,
                    color=(0, 0, 0),
                    align=align,
                )
            except Exception:
                break
            if remaining >= -0.1:
                return
            size -= 0.4

    # Last-resort fallback
    page.insert_text(
        (box.x0, box.y1 - 1.0),
        text,
        fontsize=6.0,
        fontname="helv",
        color=(0, 0, 0),
    )


def normalize_sentence(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return cleaned
    if cleaned[-1] not in ("。", "！", "？", ".", "!", "?"):
        cleaned += "。"
    return cleaned


def normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u2022", "").strip())


def extract_page_heading(page: fitz.Page, fallback: str) -> str:
    for line in page.get_text("text").splitlines():
        clean = normalize_line(line)
        if clean:
            clean = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff（）()、，。:：._\\-\\s]", "", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                return clean
    return fallback


def collect_text_blocks(page: fitz.Page) -> list[fitz.Rect]:
    blocks = page.get_text("dict").get("blocks", [])
    rects: list[fitz.Rect] = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        rect = fitz.Rect(block["bbox"])
        if rect.width < 40 or rect.height < 9:
            continue
        rects.append(rect)
    rects.sort(key=lambda r: (round(r.y0, 1), round(r.x0, 1)))
    return rects


def char_budget(rect: fitz.Rect) -> int:
    area = max(1.0, rect.width * rect.height)
    return max(28, min(260, int(area / 75.0)))


def trim_text(text: str, limit: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(1, limit - 1)] + "…"


def ascii_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return slug or "app"


def generate_source_page(cfg: DocConfig, heading: str, page_no: int) -> str:
    desc = normalize_sentence(cfg.software_description)
    mod = f"p{page_no:02d}"
    app_code = ascii_slug(cfg.software_name)
    brief = trim_text(ascii_slug(desc), 42)
    lines = [
        f"{heading}",
        f"// software: {cfg.software_name}",
        f"// version: {cfg.version}",
        f"// page: {mod}",
        "",
        f"export type {mod}_request = {{",
        "  userId: string",
        "  role: string",
        "  timestamp: number",
        "  payload: string",
        "}",
        "",
        f"export function {mod}_validate(input: {mod}_request): boolean {{",
        "  if (input.userId.length == 0) { return false }",
        "  if (input.payload.length == 0) { return false }",
        "  return true",
        "}",
        "",
        f"export function {mod}_build_message(input: {mod}_request): string {{",
        f"  const app: string = '{app_code}'",
        f"  const brief: string = '{brief}'",
        "  return app + '|' + input.role + '|' + input.userId + '|' + brief",
        "}",
        "",
        f"// note: {trim_text(desc, 78)}",
        f"// generated for software-copyright material ({cfg.software_name})",
    ]
    return "\n".join(lines)


def generate_source_block(cfg: DocConfig, heading: str, page_no: int, block_no: int) -> str:
    desc = normalize_sentence(cfg.software_description)
    func = f"moduleP{page_no:02d}B{block_no:02d}"
    app_code = ascii_slug(cfg.software_name)
    desc_code = ascii_slug(desc)
    if block_no == 0:
        return (
            f"{heading}\n"
            f"// 软件：{cfg.software_name} 版本：{cfg.version}\n"
            f"// 场景说明：{desc}"
        )
    if block_no % 3 == 1:
        return (
            f"export type {func}Input = {{\n"
            "  userId: string\n"
            "  ts: number\n"
            "  payload: string\n"
            "}"
        )
    if block_no % 3 == 2:
        return (
            f"export function {func}(input: {func}Input): string {{\n"
            f"  const app: string = '{app_code}'\n"
            f"  const brief: string = '{trim_text(desc_code, 36)}'\n"
            "  return app + '|' + input.userId + '|' + brief\n"
            "}"
        )
    return (
        f"// 测试用例 P{page_no:02d}-B{block_no:02d}\n"
        "const ok: boolean = true\n"
        "if (!ok) { throw new Error('validation failed') }"
    )


def generate_design_block(cfg: DocConfig, heading: str, page_no: int, block_no: int) -> str:
    desc = normalize_sentence(cfg.software_description)
    if block_no == 0:
        return (
            f"{heading}\n"
            f"软件：{cfg.software_name}（v{cfg.version}）\n"
            f"目标：{trim_text(desc, 72)}"
        )
    if block_no % 3 == 1:
        return (
            f"1. 功能边界：围绕“{cfg.software_name}”核心场景实现闭环。\n"
            "2. 数据约束：关键实体采用强类型定义，状态流转可追踪。"
        )
    if block_no % 3 == 2:
        return (
            "3. 交互原则：主链路操作短、反馈及时、异常有兜底。\n"
            "4. 平台差异：APP-ANDROID 与 APP-IOS 通过条件编译隔离。"
        )
    return (
        f"5. 验收口径：P{page_no:02d} 模块满足功能、性能、兼容与安全基线。\n"
        "6. 测试策略：覆盖正常、边界、弱网、异常恢复与回归场景。"
    )


def generate_design_page(cfg: DocConfig, heading: str, page_no: int) -> str:
    desc = normalize_sentence(cfg.software_description)
    return (
        f"{heading}\n"
        f"软件名称：{cfg.software_name}\n"
        f"版本：{cfg.version}\n"
        f"页码：P{page_no:02d}\n"
        f"本页目标：{trim_text(desc, 100)}\n\n"
        "1. 功能边界：围绕核心业务路径实现闭环，异常场景提供可恢复兜底。\n"
        "2. 数据约束：关键实体采用强类型定义，状态流转可审计、可追踪。\n"
        "3. 交互原则：操作路径短、反馈明确、错误提示可定位。\n"
        "4. 平台策略：Android / iOS 差异通过条件编译隔离。\n"
        "5. 验收标准：功能、性能、兼容性、安全与日志可观测性达标。"
    )


def rewrite_generated_body(doc: fitz.Document, cfg: DocConfig, doc_kind: str) -> int:
    rewrites = 0
    for page_index in range(1, doc.page_count):
        page = doc[page_index]
        heading = extract_page_heading(page, f"第{page_index + 1}页").replace(
            REFERENCE_SOFTWARE_NAME, cfg.software_name
        )
        if doc_kind == "source":
            body_box = fitz.Rect(66.0, 145.0, 548.0, 740.0)
            draw_boxed_text(page, body_box, "", align=fitz.TEXT_ALIGN_LEFT)
            draw_boxed_text(
                page,
                body_box,
                generate_source_page(cfg, heading, page_index + 1),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            rewrites += 2
            continue

        if doc_kind == "design":
            body_box = fitz.Rect(66.0, 145.0, 548.0, 740.0)
            draw_boxed_text(page, body_box, "", align=fitz.TEXT_ALIGN_LEFT)
            draw_boxed_text(
                page,
                body_box,
                generate_design_page(cfg, heading, page_index + 1),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            rewrites += 2
            continue
    return rewrites


def patch_source_cover(doc: fitz.Document, cfg: DocConfig) -> int:
    page = doc[0]
    hits = 0
    draw_boxed_text(
        page,
        fitz.Rect(120.0, 88.0, 500.0, 118.0),
        f"{cfg.software_name}移动端软件源程序清单",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    hits += 1
    draw_boxed_text(
        page,
        fitz.Rect(190.0, 124.0, 420.0, 145.0),
        f"移动端软件版本 {cfg.version}",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    hits += 1
    draw_boxed_text(page, fitz.Rect(68.0, 287.0, 540.0, 307.0), f"公司名称   {cfg.company_name}")
    draw_boxed_text(page, fitz.Rect(68.0, 308.0, 540.0, 328.0), f"作者   {cfg.author}")
    draw_boxed_text(page, fitz.Rect(68.0, 328.0, 540.0, 349.0), f"时间   {cfg.doc_date}")
    draw_boxed_text(page, fitz.Rect(68.0, 347.0, 540.0, 370.0), "")
    hits += 4
    draw_boxed_text(page, fitz.Rect(68.0, 560.0, 120.0, 584.0), "简介")
    hits += 1

    intro_box = fitz.Rect(70.0, 592.0, 548.0, 629.0)
    desc = normalize_sentence(cfg.software_description)
    intro = (
        f"{cfg.software_name}移动端软件 APP 是{cfg.company_name}自主开发的 APP，{desc}\n"
        "整体设计遵循安全、简洁、高效的工程原则。"
    )
    draw_boxed_text(page, intro_box, intro, align=fitz.TEXT_ALIGN_LEFT)
    hits += 1
    return hits


def patch_design_cover(doc: fitz.Document, cfg: DocConfig) -> int:
    page = doc[0]
    hits = 0
    draw_boxed_text(
        page,
        fitz.Rect(140.0, 88.0, 470.0, 118.0),
        f"{cfg.software_name}软件设计说明书",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    hits += 1
    draw_boxed_text(
        page,
        fitz.Rect(205.0, 124.0, 430.0, 145.0),
        f"移动端软件版本 {cfg.version}",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    hits += 1
    draw_boxed_text(page, fitz.Rect(68.0, 333.0, 540.0, 353.0), f"公司名称   {cfg.company_name}")
    draw_boxed_text(page, fitz.Rect(68.0, 354.0, 540.0, 374.0), f"作者   {cfg.author}")
    draw_boxed_text(page, fitz.Rect(68.0, 375.0, 540.0, 395.0), f"时间   {cfg.doc_date}")
    draw_boxed_text(page, fitz.Rect(68.0, 393.0, 540.0, 418.0), "")
    hits += 4

    summary_box = fitz.Rect(72.0, 430.0, 540.0, 505.0)
    desc = normalize_sentence(cfg.software_description)
    summary = (
        f"软件基本描述：{desc}\n"
        f"本文档用于《{cfg.software_name}》软件著作权申请材料，"
        "覆盖总体设计、模块职责、数据模型、交互流程与测试验收口径。"
    )
    draw_boxed_text(page, summary_box, summary, align=fitz.TEXT_ALIGN_LEFT)
    hits += 1
    return hits


def ensure_template(path: Path, expected_pages: int, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} template not found: {path}")
    with fitz.open(path) as doc:
        pages = doc.page_count
    if pages != expected_pages:
        raise ValueError(
            f"{label} template page count mismatch: expected {expected_pages}, got {pages}. "
            f"Template: {path}"
        )


def build_from_template(
    template_path: Path,
    output_path: Path,
    expected_pages: int,
    cfg: DocConfig,
    doc_kind: str,
) -> tuple[int, int]:
    with fitz.open(template_path) as doc:
        before_pages = doc.page_count
        if before_pages != expected_pages:
            raise ValueError(
                f"{doc_kind} template page count mismatch: expected {expected_pages}, got {before_pages}"
            )

        cover_hits = 0
        if doc_kind == "source":
            cover_hits = patch_source_cover(doc, cfg)
        elif doc_kind == "design":
            cover_hits = patch_design_cover(doc, cfg)

        rewrite_hits = rewrite_generated_body(doc, cfg, doc_kind)

        if output_path.exists():
            output_path.unlink()
        doc.save(output_path, garbage=4, deflate=True)

    with fitz.open(output_path) as out_doc:
        after_pages = out_doc.page_count
    if after_pages != expected_pages:
        raise ValueError(
            f"{doc_kind} output page count mismatch: expected {expected_pages}, got {after_pages}"
        )
    return cover_hits + rewrite_hits, after_pages


def main() -> int:
    args = parse_args()
    try:
        cfg = DocConfig(
            software_name=require_value(args.software_name, "请输入软件名称: "),
            company_name=require_value(args.company_name, "请输入公司名称: "),
            software_description=require_value(
                args.software_description, "请输入软件基本描述（1-3句）: "
            ),
            version=args.version.strip() or "1.0",
            author=args.author.strip() or getpass.getuser(),
            doc_date=args.doc_date.strip() or date.today().isoformat(),
            output_dir=Path(args.output_dir).expanduser().resolve(),
            template_source=Path(args.template_source).expanduser().resolve(),
            template_design=Path(args.template_design).expanduser().resolve(),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    ensure_template(cfg.template_source, SOURCE_PAGE_COUNT, "source-list")
    ensure_template(cfg.template_design, DESIGN_PAGE_COUNT, "design-spec")

    safe_name = normalize_filename(cfg.software_name)
    source_out = cfg.output_dir / f"{safe_name}源码清单.pdf"
    design_out = cfg.output_dir / f"{safe_name}软件设计说明书.pdf"

    try:
        source_hits, source_pages = build_from_template(
            template_path=cfg.template_source,
            output_path=source_out,
            expected_pages=SOURCE_PAGE_COUNT,
            cfg=cfg,
            doc_kind="source",
        )
        design_hits, design_pages = build_from_template(
            template_path=cfg.template_design,
            output_path=design_out,
            expected_pages=DESIGN_PAGE_COUNT,
            cfg=cfg,
            doc_kind="design",
        )
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 2

    print(f"[OK] {source_out}")
    print(f"[OK] {design_out}")
    print(
        "[OK] page counts: "
        f"{source_out.name}={source_pages}, {design_out.name}={design_pages}"
    )
    print(
        "[OK] replacement hits: "
        f"source={source_hits}, design={design_hits}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
