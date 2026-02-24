---
name: git-default-repo
description: Report the default git remote repository and default branch for a project. Use when a user asks which repo is the default, what the origin is, or wants the default branch.
---

# Git Default Repo

## Overview

Identify the repo root, origin URL, and default branch for the current project.

## Quick start

- Run the helper script:
  - `bash /Users/chappie/.codex/skills/git-default-repo/scripts/show_default_repo.sh /path/to/project`

## Workflow

1. Confirm you are in a git repo
2. Read origin URL and default branch
3. Report the repo root, origin, and default branch clearly

## Script reference

- `scripts/show_default_repo.sh` prints repo root, origin URL, and default branch.

## Notes

- If `origin` is missing, report it as `(none)` and ask which remote to use.
- If default branch is unknown, fall back to listing remotes and branches.
