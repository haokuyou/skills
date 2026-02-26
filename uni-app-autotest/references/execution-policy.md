# 执行策略（逻辑层）

## 命令优先级

1. Skill 内置脚本（`preflight-autotest.sh`、`run-autotest.sh`）
2. 项目内已有测试脚本（`scripts/*.sh`、`npm scripts`，仅用户明确要求时）
3. 官方 CLI 原生命令（`npx hbuilderx-cli uniapp.test ...`）

禁止先走第 3 层再回头拼装临时链路。
默认使用全局路径：`$HOME/.codex/skills/uni-app-autotest/scripts/*`，不依赖项目中是否存在同名脚本。
对 `android/ios/harmony`，默认优先官方 HBuilderX CLI 直连，不优先 npx wrapper。

## 平台约束

1. iOS 自动化仅支持 iOS Simulator（`ios` / `app-ios-simulator`）。
2. `app-ios` 视为无效平台值，必须直接返回 `BLOCKED`。
3. 预检返回 `BLOCKER` 后立即停止，不得继续执行测试命令（除非用户明确授权试跑）。
4. 预检阻塞时必须执行回退检查（不写文件）并输出可复跑命令。
5. 预检阻塞时进入“只读模式”，禁止任何代码或配置写入。

## iOS 可见性与耗时沟通

1. 用户要求“先打开 iOS 模拟器再测试”时，先激活 Simulator 前台，再执行测试命令。
2. iOS 测试前必须提示：`uniapp.test` 可能先编译全量工程，首轮可耗时数分钟。
3. iOS 测试结束后再次激活 Simulator 前台，避免结果已出但用户看不到界面。

## 重试与切换预算

1. 同一失败签名（同一错误关键词）最多重试 2 次。
2. 单任务最大策略切换数 3 次（例如：项目脚本 -> 官方命令 -> 单用例命令）。
3. 超出预算后必须返回 `BLOCKED`，并说明最小下一步。
4. 进程轮询（`ps/pgrep`）最多 3 轮；超过则直接 `BLOCKED`。
5. CLI 族切换（官方 CLI / npx wrapper / 项目脚本）最多 1 次。
6. 系统级重型修复（runtime 删除/下载、模拟器 erase）默认不执行，需用户显式授权。

## 超时策略

1. 默认命令超时：`AUTOTEST_TIMEOUT_SEC=900`。
2. 默认重试次数：`AUTOTEST_MAX_RETRIES=1`（总尝试 2 次）。
3. 超时后不得继续无限重跑，必须先给出阻塞结论或调整超时参数后再执行一次。
4. 若系统无 `timeout/gtimeout`，必须启用脚本内置 watchdog 超时，禁止无超时裸跑。

## 变更控制

1. 默认模式为“只读执行”，禁止隐式改写项目依赖与锁文件。
2. 需要安装依赖时，必须先获用户明确授权，再执行：
   - `bootstrap-autotest.sh --apply`
   - 或 `npm install/uninstall/prune`
3. 如发生非预期改写（`package.json`、`package-lock.json`、`node_modules`），优先报告影响并让用户确认处理方案。
4. 默认开启自动配置回滚：执行后恢复 `env.js` 与 `jest.config.js` 到执行前快照。
5. 在只读模式下，禁止 `apply_patch`、重定向写文件（`>`/`cat >`）、以及原地编辑命令。
6. `@dcloudio/hbuilderx-cli` 仅在项目脚本依赖它时才需要；官方 HBuilderX CLI 直连场景下视为可选。
7. Apple Silicon + x86_64-only launcher 时，仅在 CLI 含 x86_64 slice 时启用 Rosetta；CLI 为 arm64-only 时保持原生执行并继续诊断。
8. 对 `android/ios/harmony`，命令退出码为 0 仍需校验“本轮新 JSON 报告”是否生成；未生成则视为 `BLOCKED`。
9. 禁止通过修改 `PATH` 临时绕过预检逻辑；兼容性问题应在 skill 脚本修复并沉淀。
10. 官方 HBuilderX CLI 的运行端口按当前实现固定为 `9520`，自定义端口环境变量仅用于诊断提示，不作为运行端口切换。

## 证据要求

每次“继续执行”前必须至少新增一种证据：

1. 新命令输出（非重复日志）。
2. 新报告路径或新时间戳文件。
3. 新错误签名或已消失的错误签名。

若无法新增证据，停止并返回 `BLOCKED`。

预检阻塞时，以下 3 项视为最小证据集：

1. 目标测试文件存在性。
2. 测试文件语法可检查结果（若 node 可用）。
3. 一条可直接重试的标准命令。

对 `android/ios/harmony`，还需追加一项证据：
4. 与当前执行时间匹配的“新报告文件路径”（或明确声明“无新报告 -> BLOCKED”）。

## 进程治理

1. 仅终止当前会话中启动且已记录 PID 的进程。
2. 禁止 `pkill -f` 这类宽匹配清理。
3. 终止前输出 PID 与原因，终止后校验进程状态。
4. `RUN_STATUS=BLOCKED` 后禁止手工编辑项目文件；仅允许只读诊断和结果汇报。

## 临时脚本策略

1. 禁止默认在 `/tmp` 生成大脚本（尤其长 heredoc）。
2. 仅在满足全部条件时允许临时脚本：
   - 项目与 skill 中都不存在等价可复用脚本。
   - 用户明确允许。
   - 脚本长度可控且有超时/退出码处理。
3. 优先把可复用逻辑沉淀到 skill `scripts/`，不要在任务中反复重写。
