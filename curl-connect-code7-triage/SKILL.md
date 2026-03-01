---
name: curl-connect-code7-triage
description: "排查和修复 `curl: (7) Failed to connect` / `Process exited with code 7` 的连接失败循环，优先判断服务是否启动、端口是否监听、探测是否过早。Use when session logs repeat curl code 7 errors, local health checks fail repeatedly, or manual retries keep hitting 'Couldn't connect to server'."
---

# Curl Connect Code7 Triage

## Overview

在本地服务验证阶段，稳定处理 `curl (7)` 重复失败，避免“盲目重试 curl”。先确认监听状态，再做带等待的探测，并输出最小修复动作。

## Trigger signature

- `curl: (7) Failed to connect to 127.0.0.1 port <port>: Couldn't connect to server`
- `Process exited with code 7`（且输出包含 curl 连接失败）

## Workflow

1. 固定输入：目标 URL、总等待时间（默认 20 秒）。
2. 先运行诊断脚本：
   - `python3 /Users/chappie/.codex/skills/curl-connect-code7-triage/scripts/triage_curl_code7.py --url "http://127.0.0.1:5173/" --timeout 20`
3. 根据脚本结论行动：
   - `NOT_LISTENING`: 进程未监听端口，先启动服务或修正端口。
   - `BECAME_READY`: 服务晚启动，保留等待探测，不再重复裸 `curl`。
   - `STILL_UNREACHABLE`: 服务持续不可达，检查 host/port、防火墙、容器端口映射。
4. 在同一任务中若重复出现 `curl (7)` 两次以上，不再继续裸 `curl`，必须先跑脚本。

## Boundary

- 仅处理 `curl (7)` 连接失败。
- 如果核心任务是“识别并启动项目”，优先使用 `project-run-basic`。
- 如果是网络策略、代理、证书等复杂网络问题，先给最小可执行定位结果，再交由对应网络流程处理。

## Resources

### scripts/
- `triage_curl_code7.py`: 对本地 URL 做监听检查 + 等待探测，输出标准化状态和建议动作。
