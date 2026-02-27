---
name: version-bump-basic
description: Update version numbers across common project files (package.json, pyproject.toml, Cargo.toml, build.gradle, gradle.properties, Info.plist, VERSION). Use when a user asks to bump/set version, align app/build versions, says "change version to X", or uses equivalent Chinese requests such as "版本改成X"/"将版本改成X".
---

# Version Bump Basic

## Overview

Locate version fields in common project files, update to the requested version, and verify the changes.

## Quick start

- Scan for version fields:
  - `python3 /Users/chappie/.codex/skills/version-bump-basic/scripts/find_versions.py --root /path/to/project`

## Workflow

1. Confirm the target version and scope
   - Ask whether the request is about app version, build number, or both when unclear.
2. Find version fields
   - Run the scanner script and record the files/lines it reports.
3. Update version fields
   - JSON/TOML: update the `version` key.
   - Android Gradle: update `versionName` and `versionCode` if needed.
   - iOS Info.plist: update `CFBundleShortVersionString` and `CFBundleVersion` if needed.
4. Re-scan to confirm
   - Re-run the script to confirm the updated version(s) are visible.

## Script reference

- `scripts/find_versions.py` finds version-like lines in common project config files.

## Notes

- If the scan finds nothing, look for project-specific version files or build scripts.
