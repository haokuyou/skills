---
name: software-doc-pdf-pair
description: "Generate two software-copyright (软著) application PDFs as a pair: source-code manifest and software design specification. Use when users ask to produce/refresh 软件著作权材料, 源程序清单, 软件设计说明书, or explicitly request two PDF deliverables that match a reference format and page count."
---

# Software Copyright PDF Pair

## Overview

Collect required software metadata from the user and generate two PDFs with stable structure and fixed page counts based on template files:
- `《<软件名>源码清单.pdf》`
- `《<软件名>软件设计说明书.pdf》`

Generation mode:
- Keep the template layout/image positions.
- Regenerate body text blocks per page from `软件名称 + 软件基本描述` (not a full template copy).

## Required Inputs

Always collect these three fields before generation:
1. 软件名称
2. 公司名称
3. 软件基本描述（1-3 句）

Optional fields:
- 版本号（default: `1.0`）
- 作者（default: current system user）
- 输出目录（default: current working directory）
- 文档日期（default: today）

## Workflow

1. Confirm required inputs are present.
2. Use bundled template PDFs under `assets/` as format baseline.
3. Run the generator script (template-guided rewrite).
4. Verify both output PDFs have expected page counts.
5. Return absolute output paths to the user.

## Commands

Preferred command:

```bash
/Users/chappie/.codex/skills/software-doc-pdf-pair/scripts/run_softcopyright_pdf.sh \
  --software-name "你的软件名" \
  --company-name "你的公司名" \
  --software-description "你的软件基本描述" \
  --version "1.0" \
  --output-dir "/absolute/output/path"
```

Direct Python command (if dependencies already installed):

```bash
python3 /Users/chappie/.codex/skills/software-doc-pdf-pair/scripts/build_softcopyright_pdfs.py \
  --software-name "你的软件名" \
  --company-name "你的公司名" \
  --software-description "你的软件基本描述"
```

## Output Contract

- Output file 1: `<软件名>源码清单.pdf`
- Output file 2: `<软件名>软件设计说明书.pdf`
- Page counts must match template counts:
1. 源码清单: 70 页
2. 设计说明书: 52 页
- If template files are missing, stop and ask user for replacement template paths.

## Validation

After generation, verify:
1. Both PDFs exist.
2. Page counts are exactly expected.
3. Cover page metadata reflects software name/company/version/date.

## Files

- Script entry: `scripts/run_softcopyright_pdf.sh`
- Generator: `scripts/build_softcopyright_pdfs.py`
- Process notes: `references/softcopyright-workflow.md`
- Template assets:
1. `assets/template-source-list.pdf`
2. `assets/template-design-spec.pdf`
