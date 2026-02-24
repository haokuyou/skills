---
name: exec-command-oserror2
description: "Diagnose exec_command CreateProcess failures with \"No such file or directory (os error 2)\" by checking workdir existence, command paths, and executable permissions. Use when exec_command returns CreateProcess/Rejected errors (Rejected(\"Failed to create unified exec process: No such file or directory (os error 2)\")) or when a wrong workdir/relative script path is suspected."
---

# Exec Command OSError 2

## Quick start

Trigger signature:
- `exec_command failed: CreateProcess ... No such file or directory (os error 2)`

1. Run the checker to validate workdir + command path:
   - `python3 /Users/chappie/.codex/skills/exec-command-oserror2/scripts/check_exec_prereqs.py --workdir "<dir>" --cmd "<command string>"`
2. Fix the first failing item in this order: workdir -> command path -> executable bit.
3. Re-run the same exec_command with the corrected workdir or absolute command path.

## Workflow

1. Confirm `workdir` exists and matches the intended project path.
2. Resolve the command:
   - If the command is relative (e.g. `./check_build.sh`), resolve it against `workdir`.
   - If the command is a binary name (e.g. `rg`), check it exists in `PATH`.
3. If the file exists but is not executable, add execute permission before re-run.
4. If `PATH` is the issue, prefer absolute paths or an inline PATH (see `$path-update-warning`).

## Interpreting the checker output

- `WORKDIR_MISSING`: the directory does not exist. Fix the path first.
- `CMD_NOT_FOUND`: the command is not on PATH. Use absolute path or add PATH.
- `CMD_NOT_EXECUTABLE`: the file exists but is missing execute permission.
- `CMD_RESOLVED`: the command path resolves; re-run exec_command with that exact path.

## Examples

- Wrong workdir:
  - `python3 .../check_exec_prereqs.py --workdir "/Users/chappie/Documents/我制作/software/灵动触动Xcode/SmartAccess" --cmd "./check_build.sh"`
- Missing command:
  - `python3 .../check_exec_prereqs.py --workdir "/Users/chappie/project" --cmd "rg -n \"foo\" ."`

## Resources

### scripts/
- `check_exec_prereqs.py`: validate workdir + command resolution for exec_command OSError 2 failures.
