# Official References

- Main guide: https://doc.dcloud.net.cn/uni-app-x/ai/auto-test.html
- HBuilderX CLI package: https://www.npmjs.com/package/@dcloudio/hbuilderx-cli
- HBuilderX CLI docs: https://hx.dcloud.net.cn/cli/README
- uni automation API: https://uniapp.dcloud.net.cn/worktile/auto/api.html

Last verified: 2026-02-12.

## Environment Preparation

1. Install npm dependency in project root:

```bash
npm install @dcloudio/hbuilderx-cli --save-dev
```

2. Install and verify `HBuilderX uni-app` autotest plugin in HBuilderX.
3. Keep required platform toolchains available:
   - iOS: macOS + Xcode simulator (simulator only, not physical iOS device).
   - Harmony: DevEco toolchain.

## Platform Command Examples

According to the current official guide, AI CLI commonly triggers tests via npm scripts backed by
`@dcloudio/hbuilderx-cli` (e.g. `uni-test app-android`):

```bash
# Android (all)
npm run test:app-android

# Android (single case + device)
npm run test:app-android -- --testcaseFile pages/index/index.test.js --device_id emulator-5554

# iOS simulator
npm run test:app-ios

# Web / Weixin
npm run test:web -- --testcaseFile pages/index/index.test.js
npm run test:mp-weixin -- --testcaseFile pages/index/index.test.js
```

Notes:

1. iOS tests are simulator-only.
2. In our skill implementation, `android/ios/harmony` default to the official HBuilderX CLI direct path for stability.

## Suggested npm Scripts

```json
{
  "scripts": {
    "test:web": "uni-test web",
    "test:mp-weixin": "uni-test mp-weixin",
    "test:app-android": "uni-test app-android",
    "test:app-ios": "uni-test app-ios",
    "test:app-harmony": "uni-test app-harmony"
  }
}
```

## Typical AI Prompt Seed

Create `AGENT-Test-Prompt.md` in project root, then ask the AI CLI to read it and generate + run tests for the target platform.
