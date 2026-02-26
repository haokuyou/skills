# 常见阻塞排查

## iOS 平台值误用

现象示例：
- 使用 `app-ios` 后运行异常或与预期不一致。

处理建议：

1. iOS 自动化仅支持模拟器，使用 `ios` 或 `app-ios-simulator`。
2. 遇到 `app-ios` 直接改为 simulator 平台值重试。

## iOS 模拟器安装失败（架构不匹配）

现象示例：
- 提示 App 需要更新才能在当前 iOS 版本运行。
- 用例未进入断言阶段，直接运行异常。

排查命令：

```bash
xcrun simctl list runtimes
lipo -archs /Applications/HBuilderX.app/Contents/HBuilderX/plugins/uniappx-launcher/base/Pandora_simulator.app/UniAppX
```

判断规则：

1. Apple Silicon（`uname -m` 为 `arm64`）场景下，若 `UniAppX` 不包含 `arm64` slice，视为环境阻塞。
2. 若仅有高版本 iOS Runtime 且启动器不兼容，也视为环境阻塞。

处理建议：

1. Apple Silicon 且 launcher 为 x86_64-only 时，先检查 CLI 架构，只有包含 `x86_64` 才能用 Rosetta：
   - `lipo -archs /Applications/HBuilderX.app/Contents/MacOS/cli`
   - 包含 `x86_64` 时再执行：`arch -x86_64 /Applications/HBuilderX.app/Contents/MacOS/cli uniapp.test ...`
2. 若 CLI 为 arm64-only，不要强行加 `arch -x86_64`（会报 `Bad CPU type in executable`），改为原生执行。
3. 升级 HBuilderX / uniappx-launcher 到包含兼容 simulator 架构版本。
4. 或安装兼容的 iOS Runtime 后重试（需用户明确确认后再执行下载/删除步骤）。

## HBuilderX 未启动导致 CLI 静默

排查命令：

```bash
pgrep -fl HBuilderX || true
open -a HBuilderX
```

处理建议：

1. 先启动 HBuilderX，再重跑测试命令。
2. 若仍无日志输出，先判定阻塞，不要无限重试。

## Android 运行时连接失败

现象示例：
- `Failed to connect to runtime, please make sure the project is running`

判定：

1. 这是环境连通性阻塞，不是测试断言失败。
2. 不应在该阶段修改业务代码或测试逻辑。

排查建议：

1. 检查设备在线：`adb devices -l`
2. 检查代理变量：`env | rg '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)='`
3. 确保 HBuilderX 主进程已启动且与设备可通信。
4. 使用 skill 主入口重跑，避免切换多套 CLI。

## Android 多设备目标歧义（真机与模拟器同时在线）

现象示例：
- 未传 `device-id` 时命中真机而非模拟器。
- 同一命令在不同轮次命中设备不一致。

处理建议：

1. 明确传入 `device-id`（例如 `emulator-5554`）。
2. 若未传 `device-id`，`preflight-autotest.sh` 会输出 `SUGGESTED_DEVICE_ID=...`，`run-autotest.sh` 默认自动采用。
3. 若不希望自动选择，设置 `AUTOTEST_ANDROID_AUTO_SELECT_DEVICE=0` 并显式传参。

## Android 预检误报 adb unavailable（多设备/路径歧义）

现象示例：
- 预检报 `BLOCKER: adb is unavailable or no device/emulator is attached.`
- 回退检查却显示 `adb device count > 0`。

处理建议：

1. 优先固定 adb 路径：`ANDROID_ADB_PATH=$HOME/Library/Android/sdk/platform-tools/adb`。
2. 显式传入在线设备 ID 重跑（建议模拟器 ID）。
3. 用以下命令交叉确认：

```bash
$HOME/Library/Android/sdk/platform-tools/adb devices -l
$HOME/Library/Android/sdk/platform-tools/adb -s <device-id> get-state
```

## Android 端口冲突（9520 默认端口）

现象示例：
- `Port 9520 is in use, please specify another port`

处理建议：

1. 先释放占用端口再重跑，不修改测试或业务代码。
2. 官方 HBuilderX CLI 运行端口固定为 `9520`，不要通过 `AUTOTEST_ANDROID_PORT` 期望切换运行端口。

排查命令：

```bash
lsof -nP -iTCP:9520 -sTCP:LISTEN
lsof -nP -tiTCP:9520 -sTCP:LISTEN | xargs kill
```

说明：

1. skill 脚本内部已优先使用 `lsof -ti`（PID 输出），避免 awk 方言差异导致的语法错误。
2. 若仍报端口占用，按 PID 直接 kill 后重跑即可。

## iOS 端口冲突（9520 默认端口）

现象示例：
- `Port 9520 is in use`

处理建议：

1. 先释放占用端口再重跑，不修改测试或业务代码。
2. 官方 HBuilderX CLI 运行端口固定为 `9520`，不要通过 `AUTOTEST_IOS_PORT` 期望切换运行端口。

排查命令：

```bash
lsof -nP -iTCP:9520 -sTCP:LISTEN
lsof -nP -tiTCP:9520 -sTCP:LISTEN | xargs kill
```

## 命令退出 0 但无新报告

现象示例：
- CLI 返回码为 0
- 日志出现“测试运行结束（意外结束）”
- 报告目录没有新 JSON

判定：

1. 这是环境或运行链路阻塞，不是测试通过。
2. 必须按 `BLOCKED` 处理并执行 fallback 检查。

## 预检脚本出现 awk 语法错误

现象示例：
- preflight 在进入项目检查前就报 `awk` syntax error。

处理建议：

1. 不要通过改 `PATH` 去绕过脚本逻辑。
2. 升级 skill 到最新版本（已移除关键路径对 awk 的依赖）。
3. 使用统一入口重跑：`$HOME/.codex/skills/uni-app-autotest/scripts/preflight-autotest.sh ...`

## 系统缺少 timeout/gtimeout 导致长时间静默

现象示例：
- 进程持续存在但无新日志，且系统无 `timeout` / `gtimeout`。

处理建议：

1. 使用最新 `run-autotest.sh`，其内置 watchdog 超时会在 `AUTOTEST_TIMEOUT_SEC` 到达时自动中断。
2. 需要更长等待时，显式设置 `AUTOTEST_TIMEOUT_SEC`，不要无限等待。

## 平台参数异常循环（逐字符运行）

现象示例：
- 测试链路不断切换 `UNI_PLATFORM` 单字符并重复失败。

排查命令：

```bash
cat env.js
```

处理建议：

1. 将 `env.js` 恢复到仓库基线。
2. 使用标准平台值重跑（如 `ios` 或 `app-ios-simulator`，由脚本归一化）。
3. 恢复后先跑单用例，再跑全量。

## 副作用配置被改写

重点文件：
- `env.js`
- `jest.config.js`

处理建议：

1. 若改写来自测试工具，优先恢复到仓库基线。
2. 除非用户明确要求，不要持久化这类配置变更。


## Test suite failed to run / Test Suites 失败

现象示例：
- `Test suite failed to run`
- `Test Suites: 1 failed, 1 total`

处理建议：

1. 先从 `uniapp.test` 日志提取失败上下文，不要盲修：

```bash
python3 $HOME/.codex/skills/uni-app-autotest/scripts/extract-uniapp-failures.py   /path/to/uniapp.test.log
```

2. 优先定位首个失败块，常见为语法错误、模块缺失、测试入口路径错误。
3. 若失败块仅出现在 `*.test.js`，优先修测试，不要先动业务代码。



## 日志出现 error: [Circular *1]

现象示例：
- `error: [Circular *1]`

处理建议：

1. 这是循环引用的日志输出噪音，不等同于真实异常原因。
2. 先在同一失败块内向上寻找首个非循环错误信息。
3. 若需要复现，请避免对错误对象做 `JSON.stringify`，改用 `util.inspect` 或只打印 `message/stack`。



## Android SELinux 审计 denials（boot_mode）

现象示例：
- `avc: denied { read } for name="boot_mode" ...`

处理建议：

1. 这是系统审计噪音，通常不影响测试逻辑。
2. 若无崩溃/断言失败，可忽略该行并继续分析真实失败块。
