# PR: Introduce SRAF reflective quality gate
## Motivation
Agents need bounded critique/regeneration and auditable quality decisions, not unbounded self-praise.
## Architecture
Framework-neutral engine + policies + JSONL trace + optional LangGraph/CrewAI/AutoGen adapters. No upstream framework code is modified.
## Reliability and safety
Iteration/cost limits, tool allow/deny lists and explicit human-review boundary; this prototype does not authorize actions itself. Structured feedback and independent tests support quality improvement but cannot guarantee correctness.
## Community
Documented adapter protocol, deterministic fixtures, examples, CI and extension invitations. Maintainers: please review where framework-native hooks and async execution fit best; propose adapters and independent benchmark datasets.
## Validation
`pytest -q`; `ruff check src tests`; fixture benchmark. Provider-backed comparative numbers are not yet available.
