---
name: uni-app-x-uts
description: UTS (uni type script) language syntax + coding rules for uni-app x. Use when writing, reviewing, or debugging UTS code in uni-app x projects, especially .uts modules and script sections inside .uvue pages, or when migrating TypeScript/JavaScript code to UTS and you must follow UTS cross-platform constraints.
---

# uni-app x UTS

## What This Skill Is

Use this skill as the "source of truth router" for UTS: what syntax is allowed, what differs from TypeScript, and what cross-platform constraints to follow so the same code compiles to Kotlin/Swift/ArkTS/JS correctly.

This skill bundles a snapshot of the official uni-app x documentation (UTS section) under `references/upstream/`.

## How To Use (For The Agent)

1. If you are unsure whether a syntax is supported, do not guess. Search the upstream docs snapshot first:
   - Run `bash scripts/search_upstream.sh '<keyword>'` (or `bash scripts/search_upstream.sh --all '<keyword>'` for full-doc search)
   - Then open the relevant file under `references/upstream/unidocs-uni-app-x-zh/docs/uts/`
2. Prefer following the explicit "UTS vs TS differences" rules when porting code from TypeScript:
   - Read `references/upstream/unidocs-uni-app-x-zh/docs/uts/uts_diff_ts.md`
3. When targeting multiple platforms, follow the "define before use" discipline and avoid relying on platform-specific hoisting behavior:
   - See `references/upstream/unidocs-uni-app-x-zh/docs/uts/README.md` (variable hoisting section)

## Hard Rules (Default Safe Mode)

When you generate code, keep these constraints unless the upstream docs explicitly allow otherwise:

- Avoid `undefined`; prefer `null` where UTS requires it (see `uts_diff_ts.md`).
- Conditions must be boolean expressions; do not rely on truthy/falsy shortcuts (see `uts_diff_ts.md`).
- Avoid untyped object literals that become `UTSJSONObject`; prefer `type` definitions and explicit typing (see `uts_diff_ts.md` and `data-type.md`).
- Prefer "define before use" across the codebase for cross-platform consistency (see UTS `README.md`).
- If a behavior differs by platform (Android/iOS/Web/Harmony), surface it in the answer and point to the upstream doc section.

## Quick Scan For Non-Null Assertions

When you need a fast list of postfix `!` assertions in UTS/UVue code (often reviewed for crash risk), run:

```bash
python3 /Users/chappie/.codex/skills/uni-app-x-uts/scripts/scan_nonnull_assertions.py --root /path/to/project
```

## Timer Handle Null-Safety

When you see patterns like `clearTimeout(tid.value!)`, replace with a null-safe guard:

```uts
if (tid.value != null) {
  clearTimeout(tid.value)
  tid.value = null
}
```

## Reference Map

Start here to find the right authoritative file quickly:

- Entry / concepts: `references/upstream/unidocs-uni-app-x-zh/docs/uts/README.md`
- Keywords: `references/upstream/unidocs-uni-app-x-zh/docs/uts/keywords.md`
- Data types (incl. `UTSJSONObject`): `references/upstream/unidocs-uni-app-x-zh/docs/uts/data-type.md`
- Functions, async notes: `references/upstream/unidocs-uni-app-x-zh/docs/uts/function.md`
- Control flow notes (platform diffs like `for..in`): `references/upstream/unidocs-uni-app-x-zh/docs/uts/control.md`
- Modules (import/export): `references/upstream/unidocs-uni-app-x-zh/docs/uts/module.md`
- TS differences and refactor guidance: `references/upstream/unidocs-uni-app-x-zh/docs/uts/uts_diff_ts.md`
- Known issues: `references/upstream/unidocs-uni-app-x-zh/docs/uts/compiler-known-issues.md`, `references/upstream/unidocs-uni-app-x-zh/docs/uts/runtime-known-issues.md`

For `.uvue` pages and project structure context, also see:
- `references/upstream/unidocs-uni-app-x-zh/docs/page.md`

## Bundled Resources

### scripts/
- `scripts/search_upstream.sh`: fast search in the upstream docs snapshot.
- `scripts/scan_nonnull_assertions.py`: scan for postfix non-null assertions in `.uts`/`.uvue` files.

### references/
- `references/upstream/`: snapshot of the official docs used as authority.
- `references/upstream_snapshot.md`: repo URL + commit pinned for this snapshot.
- `references/ai_rules.md`: short checklist for writing safe UTS across platforms.
- `references/doc_map.md`: quick navigation to the right upstream file.

### assets/
- `assets/snippets/`: small, copy-paste-ready UTS patterns (kept minimal; prefer upstream docs for edge cases).
