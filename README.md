# Self-Reflective Agent Framework (SRAF)

![CI](https://github.com/AshraHossain/SRAF/actions/workflows/ci.yml/badge.svg)
Policy-gated evaluation and bounded regeneration for agent drafts. Apache-2.0. **Prototype scaffold, not a certified production system.** Judges are fallible, and no generated answer or tool action is automatically trustworthy.

## Architecture
`agent draft → evaluator → quality/cost gate → critique → regenerate → re-evaluate → approval boundary → downstream action`

Core is framework-neutral. Optional adapters add a LangGraph reflection node, a CrewAI reviewer task, or an AutoGen judge participant. Framework adapters do not intercept arbitrary internal tool calls; integrate the gate before external side effects.

## Windows quickstart
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
sraf --policy policies/default.json
python -m sraf.evaluation.benchmark
```

Optional: `pip install -e ".[langgraph]"`, `.[crewai]`, or `.[autogen]`. Keep provider credentials in environment variables, never in source control. The fixture judge is deterministic for CI, not meaningful LLM evaluation. For live evaluation, construct `JSONJudge(OpenAICompatible(base_url, model, api_key))` and `ConstrainedGenerator(...)`; use provider usage data for real costs rather than hardcoded per-call estimates.

Examples: `python examples/example_rag_self_correcting/run.py`, `python examples/example_sales_reflective/run.py`, `python examples/example_incident_reflective/run.py`. Each includes sample inputs and policy. A demo is `scripts/demo.ps1`. Benchmarks generate Markdown, JSON and CSV under `artifacts/benchmark` (fixture only). No real model/framework comparison is claimed.

## Safety and limitations
Policies fail closed for forbidden tools and cost ceiling, but tools supplied by framework agents can run before the adapter's final gate. Disable side-effecting tools inside upstream agents and use a separate execution service that checks an explicit human approval token. Do not store raw PII in JSONL traces. Redact or encrypt logs, rotate credentials, and validate untrusted model outputs. Calibration against human labels and real billing usage is necessary before deployment.

## Contribute
See CONTRIBUTING.md and docs tutorials. Proposed contributions: provider-usage accounting, async interfaces, framework-native hooks, independent groundedness graders, and CI-backed paired benchmarks. Submit tests and a design note for new adapters.
