---
name: evaluate-sraf-policy
description: Use this skill when adding or modifying a policy JSON or reflection adapter in SRAF.
---
# Evaluate SRAF Policy & Adapter Changes
1. Add unit tests for the policy gate rule in `tests/`.
2. Run `uv run pytest -q`.
3. Run `uv run python -m sraf.evaluation.benchmark` and inspect `artifacts/benchmark/`.
