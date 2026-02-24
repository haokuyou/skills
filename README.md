# Skills Repository

## Project Overview

This repository contains reusable Codex skills under `/Users/chappie/.codex/skills`.

## Current Features

- Skill definitions in `*/SKILL.md`
- Optional deterministic helpers in `scripts/`
- UI metadata in `agents/openai.yaml`

## Run and Build

- Validate one skill:
  - `python3 /Users/chappie/.codex/skills/.system/skill-creator/scripts/quick_validate.py <skill-folder>`

## Key Structure

- Non-system skills: `/Users/chappie/.codex/skills/*`
- System skills: `/Users/chappie/.codex/skills/.system/*`
