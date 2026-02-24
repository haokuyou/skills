# 软著双文档生成流程

## 目标

基于模板一次生成两份材料：
1. `<软件名>源码清单.pdf`（70 页）
2. `<软件名>软件设计说明书.pdf`（52 页）

## 输入字段

- 软件名称（必填）
- 公司名称（必填）
- 软件基本描述（必填，1-3 句）
- 版本号（可选，默认 1.0）
- 作者（可选）
- 输出目录（可选）

## 模板与页数约束

- 模板位置：
1. `assets/template-source-list.pdf`
2. `assets/template-design-spec.pdf`
- 生成脚本会读取模板每页标题并映射到新文档。
- 生成脚本会重写每页文本块内容（根据软件名与描述生成），并尽量保留模板版式与图片区域。
- 生成后会二次校验页数，不符合即报错。

## 执行命令

```bash
/Users/chappie/.codex/skills/software-doc-pdf-pair/scripts/run_softcopyright_pdf.sh \
  --software-name "示例软件" \
  --company-name "示例公司" \
  --software-description "用于示例演示的移动端管理系统。"
```
