#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import re


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_makefile_targets(path):
    targets = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+):", line)
            if m:
                targets.append(m.group(1))
    except Exception:
        pass
    return targets


def main():
    ap = argparse.ArgumentParser(description="Detect common run commands for a project.")
    ap.add_argument("--root", default=".", help="Project root (default: .)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    hints = []

    pkg = root / "package.json"
    if pkg.exists():
        data = read_json(pkg) or {}
        scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
        if scripts:
            for key in ("dev", "start", "serve", "preview"):
                if key in scripts:
                    hints.append(f"npm run {key}  # from package.json")
            if not hints:
                hints.append("npm run <script>  # check package.json scripts")
        else:
            hints.append("npm run <script>  # package.json found")

    makefile = root / "Makefile"
    if makefile.exists():
        targets = parse_makefile_targets(makefile)
        for key in ("run", "start", "dev"):
            if key in targets:
                hints.append(f"make {key}  # from Makefile")
        if not targets:
            hints.append("make <target>  # Makefile found")

    if (root / "pyproject.toml").exists():
        hints.append("poetry run <command>  # pyproject.toml found")

    if (root / "requirements.txt").exists():
        hints.append("python3 -m <module>  # requirements.txt found")

    if (root / "go.mod").exists():
        hints.append("go run .  # go.mod found")

    if (root / "docker-compose.yml").exists() or (root / "compose.yaml").exists():
        hints.append("docker compose up  # compose file found")

    if (root / "README.md").exists():
        hints.append("Check README.md for run instructions")

    if not hints:
        print("No common entrypoints found. Check README.md or project docs.")
        return

    for h in hints:
        print(h)


if __name__ == "__main__":
    main()
