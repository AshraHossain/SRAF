# AGENTS.md — Self-Reflective Agent Framework (SRAF)

Portable instructions for **Antigravity (Gemini)**, **Claude Code**, and other coding agents.

## What this project is
A framework-neutral policy-gated evaluation and bounded regeneration framework (`src/sraf/`):
`agent draft -> evaluator -> quality/cost gate -> critique -> regenerate -> re-evaluate -> approval boundary -> downstream action`.

## Commands
```bash
uv run pytest -q                                     # run offline unit + policy gate tests
uv run python -m sraf.evaluation.benchmark           # run deterministic benchmark suite
uv run ruff check .                                  # lint check
```

## Repo-Specific Rules
- **Fail-Closed Policy Gate**: Forbidden tools and cost ceilings must fail closed in deterministic Python (`src/sraf/`), never via prompt instructions.
- **No Side Effects Before Gate**: Upstream agent drafts must not execute side-effecting tools before passing the approval boundary.
- **Fixture-First CI**: Default tests and benchmarks use deterministic `FixtureJudge` so CI runs 100% offline.
