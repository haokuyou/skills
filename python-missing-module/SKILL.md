---
name: python-missing-module
description: Extract and resolve Python ModuleNotFoundError or ImportError missing-module failures. Use when tool output shows ModuleNotFoundError No module named or repeated Traceback blocks indicating a missing dependency.
---

# Python Missing Module

## Quick start

1. Extract missing modules from a log or stdout:
   - `python3 /Users/chappie/.codex/skills/python-missing-module/scripts/extract_missing_module.py --file <log.txt>`
2. Identify the active interpreter and environment (system vs venv).
3. Add the dependency using the project's standard tool (pip/poetry/uv/conda) and re-run.

## Workflow

1. Capture the traceback block containing `ModuleNotFoundError` or `ImportError`.
2. Use the extractor script to list missing modules.
3. Determine the Python environment used by the failing command (e.g., `python3 -V`, `which python3`).
4. Install the missing package using the project's standard workflow:
   - If a `requirements.txt` exists, add the package there before installing.
   - If `pyproject.toml` exists, prefer the project's dependency manager.
5. Re-run the failing command and confirm the error is gone.

## Notes

- Avoid installing into the wrong interpreter. Prefer the same Python binary used in the failing command.
- If multiple modules are missing, install them in one batch using the project's dependency tool.
- If the module is a local package, fix `PYTHONPATH` or the editable install instead of pip installing.

## Resources

### scripts/
- `extract_missing_module.py`: parse logs/stdout to list missing modules.
