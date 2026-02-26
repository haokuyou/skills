#!/usr/bin/env python3
import argparse
import os
import re
import sys


def extract_target_path(error_text: str) -> str | None:
    match = re.search(r"Failed to read file to update (.+?): No such file or directory", error_text)
    if match:
        return match.group(1).strip()
    match = re.search(r"Failed to read file to update (.+)$", error_text)
    if match:
        return match.group(1).strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Triage apply_patch missing-file verification failures."
    )
    parser.add_argument("--error", required=True, help="Full apply_patch error string.")
    parser.add_argument(
        "--workdir", default=os.getcwd(), help="Workdir used for the failed patch attempt."
    )
    args = parser.parse_args()

    target = extract_target_path(args.error)
    if not target:
        print("UNRECOGNIZED_ERROR")
        print("Cannot extract target path from error text. Verify the full apply_patch error string.")
        return 1

    workdir = os.path.abspath(args.workdir)
    is_abs = os.path.isabs(target)
    resolved = target if is_abs else os.path.abspath(os.path.join(workdir, target))
    exists = os.path.isfile(resolved)

    print(f"TARGET_RAW={target}")
    print(f"WORKDIR={workdir}")
    print(f"TARGET_IS_ABSOLUTE={'yes' if is_abs else 'no'}")
    print(f"TARGET_RESOLVED={resolved}")
    print(f"TARGET_EXISTS={'yes' if exists else 'no'}")

    print("ACTIONS:")
    if exists:
        print("- Target file exists. Re-run apply_patch from the same workdir.")
        print("- Confirm patch header uses *** Update File with this exact path.")
        return 0

    print("- Verify workdir is the intended repository root.")
    print("- Locate candidate file with: rg --files | rg '<filename>$'")
    if is_abs:
        print("- Absolute path is invalid in current filesystem; correct it before retry.")
    else:
        print("- Relative path does not resolve under current workdir; fix workdir or patch path.")
    print("- Use *** Add File only if task explicitly requires creating a new file.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
