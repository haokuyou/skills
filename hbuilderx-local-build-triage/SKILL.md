---
name: hbuilderx-local-build-triage
description: "归一化 HBuilderX 本地 `uniapp.test` / PluginHost 编译日志，聚类高频错误并输出最小修复动作。Use when logs contain `spawnSync ... swift-parser-cli ENOENT`, `plugin:uni:app-uvue-css` 属性不支持、`error: [Circular *1]` 伴随编译失败，或需要把本地编译报错转成可执行排查清单。"
---

# HBuilderX 本地编译排错

## 概览

将本地运行 `uniapp.test` 或 HBuilderX PluginHost 产生的编译日志转成“错误签名 + 证据路径 + 最小修复步骤”，避免人工反复 grep。

## 快速开始

1. 解析日志文件：
   - `python3 /Users/chappie/.codex/skills/hbuilderx-local-build-triage/scripts/triage_local_build_log.py /path/to/uniapp.log`
2. 解析 stdin：
   - `cat /path/to/uniapp.log | python3 /Users/chappie/.codex/skills/hbuilderx-local-build-triage/scripts/triage_local_build_log.py -`

## 标准流程

1. 收集一次完整失败日志（不要只截最后 10 行）。
2. 运行 `triage_local_build_log.py`，获取按频次排序的错误簇。
3. 对每个错误簇执行建议动作，优先处理最高频项。
4. 仅当签名变化后再重跑；签名不变时停止盲目重试。

## 内置签名与动作

1. `HBX_SWIFT_PARSER_ENOENT`
- 典型行：`spawnSync ... swift-parser-cli ENOENT`
- 动作：检查 HBuilderX 安装完整性、插件目录可执行文件是否存在、必要时重装/更新 HBuilderX。

2. `UVUE_FONT_WEIGHT_UNSUPPORTED`
- 典型行：`[plugin:uni:app-uvue-css] ERROR: property value \'600\' is not supported for \'font-weight\'`
- 动作：将数值字重改为 `normal` 或平台支持值，统一样式来源并重编译。

3. `PLUGINHOST_CIRCULAR_ERROR`
- 典型行：`error: [Circular *1],`
- 动作：向上回溯同时间窗口内第一条真实编译错误（通常是 ENOENT 或 CSS 语法限制），不要把该行当根因。

## 边界

1. 只做日志归一化与定位，不直接改项目源码。
2. 只给最小修复动作，不做无证据猜测。
3. 若日志中没有命中签名，返回原始错误行并提示补充完整日志。

## 资源

### scripts/
- `triage_local_build_log.py`：聚类本地编译日志并输出签名、计数、证据和动作建议。
