---
name: macos-audiofileopenurl-triage
description: "Diagnose macOS AudioToolbox/afinfo failures like \"Fail: AudioFileOpenURL failed\" when inspecting or reading audio files. Use when afinfo cannot open .wav/.mp3/.m4a files, when audio inspection commands fail, or when file paths/permissions/format mismatches are suspected."
---

# macOS AudioFileOpenURL Triage

## Overview

Identify why AudioToolbox or afinfo cannot open an audio file and apply a minimal fix (path, permissions, file format, or file integrity).

## Quick start

- Run the checker script with the exact file path(s):
  - `bash /Users/chappie/.codex/skills/macos-audiofileopenurl-triage/scripts/check_audiofileopenurl.sh "/absolute/path/to/file.wav"`
- If the same `Fail: AudioFileOpenURL failed` line repeats in one session, stop retrying `afinfo` manually and run the checker script once first.
- If the script reports `NOT_FOUND` or `NOT_READABLE`, fix the path or permissions first.
- If `afinfo` fails but `file` reports a non-audio type, re-export or convert the asset.

## Workflow

1. Confirm the path
   - The failure often comes from unquoted paths or glob expansion.
   - Always retry with a fully quoted absolute path.
2. Verify the file is present and readable
   - Check `ls -l` and `stat` output.
   - Ensure the file size is non-zero.
3. Identify the actual file type
   - Use `file` to detect the real format, not just the extension.
4. Re-test with afinfo
   - `afinfo "/path/to/file.wav"` should show format + duration.
5. If afinfo still fails
   - Re-export the audio from the source app.
   - Convert using `ffmpeg` if available (`ffmpeg -i in -c:a pcm_s16le out.wav`).
6. If session logs repeat `Fail: AudioFileOpenURL failed`, stop blind retries and run `check_audiofileopenurl.sh` once to collect deterministic evidence.

## Decision checklist

- If the path includes spaces: always wrap in quotes.
- If the file is zero bytes: regenerate or redownload.
- If `file` reports `text`/`data`: the file is not audio; fix the export.
- If `afinfo` fails only on some files: compare a known-good file vs a bad one.

## Script usage

- Single file:
  - `bash /Users/chappie/.codex/skills/macos-audiofileopenurl-triage/scripts/check_audiofileopenurl.sh "/abs/path/file.wav"`
- Multiple files (glob):
  - `bash /Users/chappie/.codex/skills/macos-audiofileopenurl-triage/scripts/check_audiofileopenurl.sh "/abs/path/*.wav"`
- Batch triage (directory):
  - `bash /Users/chappie/.codex/skills/macos-audiofileopenurl-triage/scripts/check_audiofileopenurl.sh "/abs/path/to/dir/*"`

## Notes

- `AudioFileOpenURL failed` is usually caused by a bad path, unreadable file, or invalid/unsupported audio format.
- `afinfo` is provided by macOS; if it is missing, install Xcode command line tools.

## Resources

### scripts/
- `check_audiofileopenurl.sh`: verify path, file type, size, and afinfo output for audio files.
