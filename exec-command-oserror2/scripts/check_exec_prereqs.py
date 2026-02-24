#!/usr/bin/env python3
import argparse
import os
import shlex
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check exec_command workdir/command for OSError 2.")
    parser.add_argument("--workdir", required=True, help="Working directory passed to exec_command")
    parser.add_argument("--cmd", required=True, help="Command string passed to exec_command")
    args = parser.parse_args()

    workdir = os.path.expanduser(args.workdir)
    cmd = args.cmd.strip()

    issues = []
    if not os.path.isdir(workdir):
        issues.append(f"WORKDIR_MISSING: {workdir}")

    try:
        tokens = shlex.split(cmd)
    except ValueError as exc:
        issues.append(f"CMD_PARSE_ERROR: {exc}")
        tokens = []

    if not tokens:
        issues.append("CMD_EMPTY: no command tokens parsed")
    else:
        cmd0 = tokens[0]
        resolved = None
        if cmd0.startswith("./") or cmd0.startswith("../"):
            resolved = os.path.abspath(os.path.join(workdir, cmd0))
        elif os.path.isabs(cmd0):
            resolved = cmd0
        else:
            resolved = shutil.which(cmd0)

        if resolved is None:
            issues.append(f"CMD_NOT_FOUND: {cmd0}")
        else:
            if not os.path.exists(resolved):
                issues.append(f"CMD_MISSING_PATH: {resolved}")
            elif not os.access(resolved, os.X_OK):
                issues.append(f"CMD_NOT_EXECUTABLE: {resolved}")
            else:
                issues.append(f"CMD_RESOLVED: {resolved}")

    print("exec_command OSError 2 prereq check")
    print("===============================")
    print(f"workdir: {workdir}")
    print(f"cmd: {cmd}")
    print("\nFindings:")
    for item in issues:
        print(f"- {item}")

    if any(item.startswith("WORKDIR_MISSING") for item in issues):
        print("\nNext: fix workdir path first; re-run the command from the correct directory.")
    elif any(item.startswith("CMD_NOT_FOUND") for item in issues):
        print("\nNext: use absolute command path or set PATH inline for exec_command.")
    elif any(item.startswith("CMD_NOT_EXECUTABLE") for item in issues):
        print("\nNext: chmod +x the script/binary, then re-run.")
    elif any(item.startswith("CMD_RESOLVED") for item in issues):
        print("\nNext: re-run exec_command with the resolved command path above.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
