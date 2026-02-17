---
name: uni-app-autotest
description: 使用 @dcloudio/hbuilderx-cli 与 HBuilderX uni-app 自动化测试插件，自动完成 uni-app x 测试用例编写、执行与失败修复，包含对特定组件（如 native-waterfall）在 Android/iOS 平台的测试编写与运行。适用于生成或更新 *.test.js、运行 web/weixin/android/ios-simulator/harmony 测试、分析 uniapp.test 日志与报告、持续修复失败用例等场景。
---

# uni-app x 自动化测试流程

## 前置条件

1. 在 uni-app x 项目根目录执行。
2. 本机可用 Node.js 与 npm。
3. 已安装并可使用 HBuilderX 与 `HBuilderX uni-app` 自动化测试插件。
4. Skill 脚本目录固定为 `$HOME/.codex/skills/uni-app-autotest/scripts`。
5. 首次运行建议先执行 `$HOME/.codex/skills/uni-app-autotest/scripts/bootstrap-autotest.sh <project-dir>`（默认仅检查，不修改项目）。

## 标准闭环

1. 阅读 `references/official-doc.md`，确认目标平台。
2. 执行 `$HOME/.codex/skills/uni-app-autotest/scripts/preflight-autotest.sh <platform> [project-dir] [device-id]` 做平台预检。
3. 扫描目标页面文件（`*.uvue`），生成或更新同级 `*.test.js`。
4. 按 `references/test-conventions.md` 编写与修复测试。
5. 使用 `$HOME/.codex/skills/uni-app-autotest/scripts/run-autotest.sh <platform> [case-file] [project-dir] [device-id]` 运行。
6. 抓取失败输出，修复测试逻辑或页面逻辑。
7. 持续重跑，直到通过或遇到环境阻塞。
8. 预检返回 `BLOCKER` 时，执行 `$HOME/.codex/skills/uni-app-autotest/scripts/fallback-autotest.sh` 产出非侵入式回退检查包，然后停止测试执行。
9. `BLOCKER` 后进入只读模式：禁止任何项目写操作（包括修改 `*.test.js`、`*.uvue`、配置文件）。

## 目标定位协议

1. 先用 skill 内置入口定位目标，不先写临时脚本：
   - `$HOME/.codex/skills/uni-app-autotest/scripts/preflight-autotest.sh`
   - `$HOME/.codex/skills/uni-app-autotest/scripts/run-autotest.sh`
   - 已存在的 `*.test.js`
2. 项目自带包装脚本（如 `hx-uniapp-test.sh`）默认不使用；仅在用户明确要求时使用。
3. 若目标无法定位，最多执行 3 轮定位尝试，每轮必须有可验证证据（文件路径、命令输出、日志关键字）。
4. 三轮后仍无法定位时，直接按 `BLOCKED` 返回，不继续扩展临时命令链。
5. 目标定位失败时，向用户请求更精确锚点（页面路径、脚本名、测试文件名三选一即可）。

## native-waterfall 快速定位（Android/iOS）

1. 先运行只读扫描脚本定位页面与测试文件：
   - `$HOME/.codex/skills/uni-app-autotest/scripts/find-native-waterfall.sh <project-dir>`
2. 优先锁定以下路径中的页面与用例：
   - `uni_modules/native-waterfall/**`
   - `pages/**/native-waterfall*.uvue`
   - `**/*native-waterfall*.test.js`
3. 找到页面与用例后再执行 `preflight-autotest.sh` 与 `run-autotest.sh`，避免在未定位页面时盲跑。

## 用例生成规则

1. 测试文件尽量与页面文件同级放置。
2. 使用 `*.test.js` 命名，确保 Jest 可发现。
3. 用例必须独立，不依赖执行顺序。
4. 优先使用稳定选择器与显式等待，避免无意义 sleep。
5. 关键页面至少覆盖一个主流程和一个异常/边界流程。
6. 遇到不稳定用例优先做确定性 setup/teardown，不先堆重试。

## 执行规则

1. 如项目已定义平台脚本，优先执行：
   - `test:uniappx:web`
   - `test:uniappx:weixin`
   - `test:uniappx:android`
   - `test:uniappx:ios`（iOS 模拟器）
   - `test:uniappx:harmony`
2. 对 `android/ios/harmony`，默认使用官方 HBuilderX CLI：`/Applications/HBuilderX.app/Contents/MacOS/cli uniapp.test ...`。
3. 项目脚本仅作为后备选项，不得替代 skill 主入口。
4. 对 `web/weixin` 未定义脚本时，回退到 `npx hbuilderx-cli uniapp.test --platform <platform> [--case <file>]`。
5. `--testcaseFile` 统一使用项目内相对路径（避免绝对路径解析异常）。
6. 接受平台别名并归一化：`h5->web`、`mp-weixin->weixin`、`app-ios-simulator->ios`、`app-android->android`。
7. `app-ios` 视为无效参数并直接阻塞；iOS 仅支持 simulator。
8. 调试阶段先跑单用例，再跑平台全量。
9. 从 `uniapp.test` 日志中提取最新 JSON 报告路径并记录。
10. iOS 需 macOS + Xcode 模拟器，Harmony 需 DevEco 工具链。
11. 统一使用执行守卫：`AUTOTEST_TIMEOUT_SEC`（默认 900 秒）和 `AUTOTEST_MAX_RETRIES`（默认 1 次重试）。
12. 默认启用 `AUTOTEST_AUTO_RESTORE=1`，自动恢复被测试器改写的 `env.js` 与 `jest.config.js`。
13. Apple Silicon + x86_64-only iOS launcher 场景下，仅当 HBuilderX CLI 本身支持 x86_64 时才加 Rosetta (`arch -x86_64`)；若 CLI 为 arm64-only，则保持原生执行并给出告警。
14. `run-autotest.sh` 若出现“命令退出 0 但无新 JSON 报告”，必须按 `BLOCKED` 处理并执行回退检查，不得视为通过。
15. 若系统缺少 `timeout/gtimeout`，`run-autotest.sh` 必须启用内置 watchdog 超时，避免长时间静默挂起。

## 命令策略与边界

1. 禁止在未获用户明确要求时编写大体量临时脚本（例如 `/tmp/*.sh` 数十行 heredoc）。
2. 优先复用现有命令链：`preflight-autotest.sh` -> `run-autotest.sh` -> 项目已有脚本。
3. 同一失败签名最多重试 2 次；超过则归类为阻塞并返回。
4. 单次任务内最多切换 3 种执行策略；超过则停止并返回阻塞结论。
5. 长命令必须可观测：要么实时输出，要么写日志文件并在结果中给出路径。
6. 如需终止进程，只能终止“当前命令启动并记录过 PID”的进程，禁止 `pkill -f` 广泛清理。
7. 默认禁止写入项目依赖与配置；仅在用户明确同意后才执行 `bootstrap-autotest.sh --apply`。
8. 禁止“只报阻塞即结束”；必须输出回退检查结果（case 文件存在性、语法检查、可复跑命令）。
9. 进程巡检上限 3 轮（含 `ps/pgrep`）；超过上限直接阻塞返回，不继续轮询。
10. 预检阻塞时只允许执行只读诊断命令；禁止 `apply_patch`、重写文件、`cat > file`、`sed -i`。
11. 禁止在单次任务中切换多个 CLI 族（官方 CLI / npx wrapper / 项目脚本）反复试错；最多允许一次切换。
12. 禁止自动执行系统级重型修复命令（如 `xcodebuild -downloadPlatform ...`、`xcrun simctl runtime delete`、`xcrun simctl erase`）；仅在用户明确授权后执行。
13. 禁止通过改写 `PATH` 来绕过预检分支；脚本兼容问题应回到 skill 脚本修复。

## 安全规则

1. 不得在未获得用户明确同意的情况下修改项目配置文件（含 `env.js`、`jest.config.js`、`package.json`）。
2. 若工具污染了 `env.js` 或 `jest.config.js`，仅允许“恢复到仓库基线”的最小修复，并在输出中明确说明。
3. 不得随意 kill 非当前测试链路进程；只处理本次执行产生的进程。
4. 命令长时间无日志输出时，先判定为环境阻塞并上报，不得盲目循环重试。
5. 不得在未获授权时执行 `npm install`、`npm uninstall`、`npm prune` 等会改写依赖树的命令。
6. 当 `run-autotest.sh` 输出 `CODE_EDIT_ALLOWED=false` 时，必须停止所有代码与配置编辑。

## 失败处理

1. 端口冲突时，释放官方 CLI 运行端口 `9520` 后重跑；不要把 `AUTOTEST_ANDROID_PORT/AUTOTEST_IOS_PORT` 当作运行端口切换。
2. 依赖或插件缺失时，重跑 bootstrap 并验证插件安装。
3. iOS 出现安装失败或架构不匹配时，先运行 `references/troubleshooting.md` 的 iOS 检查命令并阻塞返回。
4. 纯环境问题导致失败时，输出精确阻塞点与人工步骤。
5. 断言失败时，先判断业务行为是否正确，再决定修测还是修业务。
6. 发现平台参数异常循环（按单字符逐个运行）时，立即停止当前运行并检查 `env.js` 污染。
7. 连续出现“无进展执行”时（超时或无新证据），停止尝试并返回阻塞，不继续叠加新策略。
8. iOS 预检失败后不得继续“强行执行”测试命令，除非用户明确要求试跑。
9. iOS 预检失败后，不得“先补测试再等环境修复”；默认保持代码不变并返回阻塞结论。
10. Android 运行时连接失败（`Failed to connect to runtime`）按环境阻塞处理，不归类为断言失败。
11. Android 若出现 `Port 9520 is in use`（或 `AUTOTEST_ANDROID_PORT` 对应端口冲突），先释放端口再重跑，不做代码改动。
12. iOS 若出现 `Port 9520 is in use`（或 `AUTOTEST_IOS_PORT` 对应端口冲突），先释放端口再重跑，不做代码改动。
13. `CODE_EDIT_ALLOWED=false` 或 `RUN_STATUS=BLOCKED` 后，禁止手工编辑项目文件（包括 `jest.config.js`、`env.js`）；仅允许只读诊断与回退输出。

## 资源映射

- `scripts/bootstrap-autotest.sh`：初始化 npm 依赖与可选脚本。
- `scripts/preflight-autotest.sh`：运行前预检（含 iOS 运行时与架构检查）。
- `scripts/run-autotest.sh`：按平台运行测试，支持单用例。
- `scripts/fallback-autotest.sh`：预检阻塞后的非侵入式回退检查与可复跑命令输出。
- `scripts/find-native-waterfall.sh`：定位 native-waterfall 相关页面与测试文件（只读扫描）。
- `references/official-doc.md`：官方安装与命令摘要。
- `references/test-conventions.md`：测试编写规范与检查清单。
- `references/AGENT-Test-Prompt.md`：AI CLI 可复用指令模板。
- `references/troubleshooting.md`：常见阻塞问题与排查命令。
- `references/execution-policy.md`：命令优先级、重试预算、超时与阻塞判定。

## 输出约定

1. 返回执行命令列表。
2. 返回新增/修改的测试文件路径。
3. 返回按平台统计的通过/失败结果。
4. 若被阻塞，返回精确阻塞原因与下一条人工命令。
