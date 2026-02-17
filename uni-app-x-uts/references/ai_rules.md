# UTS AI Coding Rules (Checklist)

Use this checklist when generating or refactoring UTS for uni-app x.

## If Unsure, Don't Guess

- Search upstream snapshot first: `bash scripts/search_upstream.sh '<keyword>'`
- Open the exact upstream file under `references/upstream/unidocs-uni-app-x-zh/docs/uts/` and follow it.

## Default Safe Cross-Platform Rules

- Define before use (avoid relying on platform hoisting differences). See upstream: `docs/uts/README.md` (variable hoisting section).
- Avoid `undefined`; use `null` and explicit union types where applicable. See upstream: `docs/uts/uts_diff_ts.md`.
- Do not use truthy/falsy shortcuts in conditions; conditions must be boolean. See upstream: `docs/uts/uts_diff_ts.md`.
- Prefer explicit typing for object literals; avoid accidental `UTSJSONObject` unless you intentionally want it. See upstream: `docs/uts/uts_diff_ts.md`, `docs/uts/data-type.md`.
- When porting TS code, verify each TS feature is supported and allowed in UTS. Start at: `docs/uts/uts_diff_ts.md`.

## When Answering Users

- If the behavior depends on platform (Android/iOS/Web/Harmony), call it out explicitly.
- If the behavior depends on HBuilderX/uni-app x version, call it out explicitly (with the version mentioned upstream), or recommend the user verify their version.

