# Graph Report - SRAF  (2026-11-16)

## Corpus Check
- Corpus is ~7,495 words - fits in a single context window. You may not need a graph.

## Summary
- 124 nodes · 214 edges · 18 communities (8 shown, 5 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12

## God Nodes (most connected - your core abstractions)
1. `ReflectionEngine` - 26 edges
2. `Policy` - 20 edges
3. `Evaluation` - 13 edges
4. `FixtureJudge` - 11 edges
5. `FixtureGenerator` - 9 edges
6. `ReflectionEngine — core engine running judge/generator loop` - 9 edges
7. `engine()` - 8 edges
8. `Policy Gate` - 7 edges
9. `Reflection Pipeline` - 7 edges
10. `FastAPI HTTP service layer (src/sraf/api/) gated behind optional api dep group` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Fail-Closed Rule (AGENTS.md)` --semantically_similar_to--> `Fail-Closed on Forbidden Tools`  [INFERRED] [semantically similar]
  AGENTS.md → .claude/rules/policy-gate.md
- `Policy` --uses--> `engine()`  [INFERRED]
  src/sraf/core/models.py → tests/test_engine.py
- `Policy` --uses--> `test_cost_ceiling()`  [INFERRED]
  src/sraf/core/models.py → tests/test_engine.py
- `FixtureGenerator` --uses--> `engine()`  [INFERRED]
  src/sraf/core/providers.py → tests/test_engine.py
- `FixtureJudge` --uses--> `engine()`  [INFERRED]
  src/sraf/core/providers.py → tests/test_engine.py

## Import Cycles
- None detected.

## Communities (18 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (18): Fail-Closed Rule (AGENTS.md), Fixture-First CI Policy, No Side Effects Before Gate, Deterministic Python Gate Rule, Fail-Closed on Forbidden Tools, Evaluate SRAF Policy Skill, Approved Flag (not authority), Human Approval Token (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (7): Protocol, Generator, Judge, Evaluation, JSONJudge, OpenAICompatible, Opt-in local/provider API; configure trusted HTTPS host and key outside source…

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (9): main(), Policy, ConstrainedGenerator, FixtureGenerator, FixtureJudge, Deterministic smoke-test judge; NOT a reliable hallucination detector., run(), JSONLStore (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (6): ReflectionEngine, run_chat_with_judge(), run_crew_with_review(), build_graph(), State, TypedDict

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (14): AutoGen reflective adapter (src/sraf/framework_adapters/autogen_reflective_adapter.py), CLI entry point (src/sraf/cli.py) — main(), CrewAI reflective adapter (src/sraf/framework_adapters/crewai_reflective_adapter.py), JSONLStore — observability store writing JSONL trace files, LangGraph reflective adapter (src/sraf/framework_adapters/langgraph_reflective_adapter.py), Core models: Policy, Evaluation, RunMetadata, ReflectionResult, Providers: FixtureJudge, FixtureGenerator, OpenAICompatible, JSONJudge, ConstrainedGenerator, Rationale: Fail-closed policy — forbidden tools and cost ceilings raise ValueError in pure Python, never via prompts (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.22
Nodes (13): FastAPI app factory create_app(api_key, rate_limit) (src/sraf/api/app.py), Security middleware: APIKeyMiddleware, SlidingWindowRateLimiter, SecurityHeadersMiddleware, sanitize_string, FastAPI routes: GET /health, GET /readyz, POST /reflect (src/sraf/api/routes.py), API Pydantic schemas: ReflectRequest, ReflectResponse, HealthResponse (src/sraf/api/schemas.py), ARCHITECTURE.md — Mermaid layered system + end-to-end sequence diagrams, Pure Python library core (src/sraf/core/) — zero-dependency, Design spec: docs/superpowers/specs/2026-11-16-sraf-enterprise-upgrade-design.md (Option B: FastAPI layer), Dockerfile — multi-stage build, non-root UID 10001 (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.47
Nodes (3): now(), ReflectionResult, RunMetadata

### Community 7 - "Community 7"
Cohesion: 0.43
Nodes (5): engine(), test_action_requires_approval(), test_cost_ceiling(), test_no_evidence_does_not_pass(), test_tool_blocked()

## Knowledge Gaps
- **24 isolated node(s):** `sraf`, `SRAF Project`, `No Side Effects Before Gate`, `Deterministic Python Gate Rule`, `Fail-Closed on Forbidden Tools` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 41 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ReflectionEngine` connect `Community 3` to `Community 1`, `Community 2`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `Policy` connect `Community 2` to `Community 1`, `Community 3`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Evaluation` connect `Community 1` to `Community 2`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `ReflectionEngine` (e.g. with `ReflectionResult` and `RunMetadata`) actually correct?**
  _`ReflectionEngine` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Policy` (e.g. with `Generator` and `ReflectionEngine`) actually correct?**
  _`Policy` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Evaluation` (e.g. with `Judge` and `ReflectionEngine`) actually correct?**
  _`Evaluation` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `FixtureJudge` (e.g. with `Evaluation` and `engine()`) actually correct?**
  _`FixtureJudge` has 4 INFERRED edges - model-reasoned connections that need verification._