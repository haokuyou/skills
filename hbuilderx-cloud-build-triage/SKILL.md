---
name: hbuilderx-cloud-build-triage
description: 解析 HBuilderX 云打包/云编译错误日志，抽取 UTS/原生编译错误、文件路径与行号并归一化签名，适用于收到“云打包编译错误信息”或 build.log 片段需要快速定位原因与复现入口的场景。
---

# HBuilderX 云打包错误归一化

## 概览

用脚本把 HBuilderX 云打包/云编译日志归一化成可定位的错误清单，输出文件路径、行号、错误摘要与可复现的最小片段，便于快速定位 UTS 插件与平台差异问题。

## 标准流程

1. 收集云打包错误日志（原始日志或用户粘贴片段）。
2. 使用脚本归一化输出：
   - `$HOME/.codex/skills/hbuilderx-cloud-build-triage/scripts/triage_cloud_build_log.py <log-file>`
3. 依据输出的 `FILE:LINE` 与 `SIGNATURE` 回溯到 UTS 插件或生成代码位置。
4. 若涉及 `uni_modules/native-waterfall` 或 `app-ios/app-android`，在结论中标注平台与模块范围。
5. 若日志包含 `Error code` / `Error message` 或 UTS 已知问题链接（如 error18），保留对应行并指出需参考 UTS 已知问题文档（参见 `uni-app-x-uts`）。

## 规则

1. 只做日志解析与定位，不直接修改项目文件。
2. 优先输出“可复现定位信息”：文件路径、行号、编译器错误摘要。
3. 避免长篇猜测；仅根据日志中的错误行做结论。
4. 需要更多上下文时，明确请求补充完整日志或源码片段。

## 脚本用法

1. 解析文件：
   - `triage_cloud_build_log.py /path/to/build.log`
2. 解析 stdin：
   - `cat build.log | triage_cloud_build_log.py -`

输出包含：
- `ERRORS`: 归一化后的错误条目（含文件与行号）
- `SIGNATURES`: 错误签名列表（去除 __UNI__ hash 与时间戳）
- `SUSPECT MODULES`: 可能涉及的 uni_modules
- `NOFILE` 行：无文件路径的错误提示（例如 `Error code` / `Error message` / error18）

## 触发示例

- “以下是 HBuilderX 云打包编译错误信息，分析一下是什么原因？”
- “UTS plugin xxx compile error / Build failed with an exception”
- “app-ios/app-android 云编译失败，请定位出错文件”
