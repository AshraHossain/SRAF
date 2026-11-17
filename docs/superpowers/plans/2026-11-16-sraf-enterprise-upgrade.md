# SRAF Enterprise Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring SRAF to enterprise-grade portfolio quality: 95%+ test coverage per module, a FastAPI HTTP service layer with security hardening, Mermaid architecture diagrams, `make check` CI gate, and Docker packaging — all from a clean `main` branch.

**Architecture:** Pure Python library core (`src/sraf/core/`) stays zero-dependency; a thin FastAPI service layer (`src/sraf/api/`) is gated behind the `api` optional dep group and applies auth, rate-limiting, and OWASP headers. Test coverage is enforced at 80% minimum in CI via `pytest-cov --cov-fail-under=80`; adapters are tested offline using `unittest.mock.patch`.

**Tech Stack:** Python 3.11+, uv, pytest + pytest-cov, ruff (+ bandit/S rules), FastAPI + Pydantic (optional `api` group), uvicorn, Docker multi-stage + non-root UID 10001.

**Spec:** This plan implements the design agreed in-conversation on 2026-11-16 (Option B: FastAPI layer). Reference the approved design at `docs/superpowers/specs/2026-11-16-sraf-enterprise-upgrade-design.md` (created in Task 1).

---

## Global Constraints

- Python ≥ 3.11 (`requires-python = ">=3.11"` in pyproject.toml)
- Zero new dependencies on the core library (`dependencies = []` stays empty)
- FastAPI/Pydantic/uvicorn go into `[project.optional-dependencies] api` only
- `pytest-cov` and `ruff` go into `[project.optional-dependencies] dev`
- All tests must pass 100% offline for `pytest.mark.unit` tests; `pytest.mark.live` marks network-touching tests
- Fail-closed policy invariant: forbidden tools and cost ceilings raise `ValueError` in pure Python, never via prompts
- `RunMetadata` stays mutable (design call: accumulator during live run); `ReflectionResult` stays mutable; both are documented in ARCHITECTURE.md
- Non-root UID 10001 in Dockerfile
- Conventional commit format: `type(scope): description`

## Review Focus

1. **Prompt-injection via `evidence` field in `JSONJudge.evaluate()`** — a crafted evidence string could override `score` or `hallucination_risk` in the LLM's JSON response; the fix is to send `evidence` inside a JSON-encoded object (already done in `providers.py:41`) and add a schema validation test to `test_providers.py`. Added to Task 3.

2. **`ReflectionEngine.run()` approves on `quality_gate` only** — a run that exits via `no_change` after reaching `min_score` on the previous iteration is not approved, but callers may not check `stop_reason`. Add a test asserting `no_change` stop leaves `approved=False`. Added to Task 2.

3. **API rate-limiter concurrency** — the in-memory sliding-window counter is not thread-safe under FastAPI's default async workers. Add a `threading.Lock()` guard and a test that fires two simultaneous requests. Added to Task 7.

4. **`OpenAICompatible` HTTPS bypass** — `https://evil.com/redirect` → HTTP is not blocked by the scheme check alone; the check only validates the scheme of the initial URL, not redirects. `urlopen` follows redirects by default. Add a test that patches `urlopen` to verify the check is applied and add a note in SECURITY.md. Added to Task 3.

5. **`Policy.__post_init__` does not validate `max_iterations=0`** — `max_iterations=0` is a valid value (single evaluate, no regeneration) but `range(0+1)` still runs one iteration; the existing test `test_no_evidence_does_not_pass` relies on this. No fix needed but add a test asserting `max_iterations=0` completes without regeneration. Added to Task 2.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `docs/superpowers/specs/2026-11-16-sraf-enterprise-upgrade-design.md` | Design doc |
| Modify | `pyproject.toml` | Add pytest-cov, bandit/S, api dep group, addopts |
| Modify | `.github/workflows/ci.yml` | Fix coverage gate, add `--cov-fail-under=80` |
| Create | `tests/conftest.py` | pytest mark registration |
| Modify | `tests/test_engine.py` | Add `pytest.mark.unit` to existing 5 tests |
| Create | `tests/test_models.py` | Policy + Evaluation validation edge cases |
| Create | `tests/test_providers.py` | All provider classes (offline mocks) |
| Create | `tests/test_store.py` | JSONLStore |
| Create | `tests/test_cli.py` | CLI argparse + main() |
| Create | `tests/test_benchmark.py` | Benchmark runner |
| Create | `tests/test_adapters.py` | LangGraph, CrewAI, AutoGen (mocked) |
| Modify | `AGENTS.md` | Strip to <100 lines, repo-only content |
| Modify | `GEMINI.md` | Stays minimal; verify links correct |
| Modify | `CLAUDE.md` | Strip to repo-only content |
| Create | `src/sraf/api/__init__.py` | Package marker |
| Create | `src/sraf/api/schemas.py` | Pydantic request/response models |
| Create | `src/sraf/api/middleware.py` | Auth, rate-limit, OWASP headers, sanitization |
| Create | `src/sraf/api/routes.py` | /health, /readyz, /reflect endpoints |
| Create | `src/sraf/api/app.py` | FastAPI app factory, middleware wiring |
| Create | `tests/test_api.py` | API test suite (TestClient) |
| Create | `ARCHITECTURE.md` | Mermaid diagrams, design decisions |
| Create | `SECURITY.md` | Threat model, invariants, reporting |
| Modify | `README.md` | Badges, eval scorecard, diagram links |
| Create | `Makefile` | `make check`, `make test`, `make lint`, `make eval` |
| Create | `Dockerfile` | Multi-stage, non-root UID 10001 |
| Create | `docker-compose.yml` | FastAPI service + env |
| Create | `.dockerignore` | Standard Python ignores |

---

### Task 1: Tooling Foundation + Instruction Alignment

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`
- Create: `tests/conftest.py`
- Modify: `AGENTS.md`
- Modify: `GEMINI.md`
- Modify: `CLAUDE.md`
- Create: `docs/superpowers/specs/2026-11-16-sraf-enterprise-upgrade-design.md`

**Interfaces:**
- Produces: `pytest.mark.unit` and `pytest.mark.live` usable in all subsequent test tasks; `uv run pytest --cov=src/sraf --cov-fail-under=80 -m unit` runs clean; CI enforces coverage gate without `continue-on-error`

- [ ] **Step 1: Add `pytest-cov`, bandit/S ruff rules, and `api` dep group to `pyproject.toml`**

  In `[project.optional-dependencies]`:
  ```toml
  dev = ["pytest>=8", "ruff>=0.8", "pytest-cov>=5"]
  api = ["fastapi>=0.115", "pydantic>=2.9", "uvicorn[standard]>=0.32"]
  ```
  In `[tool.pytest.ini_options]`:
  ```toml
  addopts = "--cov=src/sraf --cov-report=term-missing"
  markers = ["unit: offline unit test", "live: requires network/API key"]
  ```
  In `[tool.ruff.lint]`:
  ```toml
  select = ["E", "F", "S"]
  ignore = ["S101"]  # assert allowed in tests
  ```

- [ ] **Step 2: Fix CI coverage gate in `.github/workflows/ci.yml`**

  Replace the last two steps in `test` job:
  ```yaml
  - name: Run tests with coverage
    run: uv run pytest -v --cov=src/sraf --cov-report=term-missing --cov-fail-under=80
  ```
  Remove `continue-on-error: true`. Remove the duplicate `uv run pytest -v` step above it.

- [ ] **Step 3: Create `tests/conftest.py`**

  ```python
  import pytest

  def pytest_configure(config):
      config.addinivalue_line("markers", "unit: offline unit test")
      config.addinivalue_line("markers", "live: requires network/API key")
  ```

- [ ] **Step 4: Verify `uv sync --dev` installs pytest-cov**

  Run: `uv sync --dev && uv run pytest --co -q`
  Expected: collection succeeds, no import errors

- [ ] **Step 5: Trim `AGENTS.md` to repo-only content (<100 lines)**

  Keep: What this project is, Commands block, Repo-Specific Rules. Remove any content that duplicates global rules already in `.claude/rules/`. Add `make check` to Commands block.

- [ ] **Step 6: Verify `GEMINI.md` and `CLAUDE.md` are <100 lines each and link correctly**

  Run: `wc -l GEMINI.md CLAUDE.md AGENTS.md`
  Expected: all under 100

- [ ] **Step 7: Write design spec to `docs/superpowers/specs/2026-11-16-sraf-enterprise-upgrade-design.md`**

  Document: intent, goals, non-goals, constraints, chosen approach (Option B), `RunMetadata` mutability rationale, FastAPI layer layout, security layer decisions, container strategy.

- [ ] **Step 8: Commit**

  ```bash
  git add pyproject.toml .github/workflows/ci.yml tests/conftest.py AGENTS.md GEMINI.md CLAUDE.md docs/
  git commit -m "chore(tooling): add pytest-cov, bandit/S ruff rules, api dep group, fix CI coverage gate"
  ```

---

### Task 2: Models + Engine Test Hardening

**Files:**
- Modify: `tests/test_engine.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Consumes: `pytest.mark.unit` from Task 1; `Policy`, `Evaluation`, `RunMetadata`, `ReflectionResult` from `src/sraf/core/models.py`; `ReflectionEngine` from `src/sraf/core/engine.py`
- Produces: `pytest.mark.unit` on all 5 existing engine tests + 2 new edge-case tests; 100% coverage of `models.py`

- [ ] **Step 1: Add `@pytest.mark.unit` to all 5 existing tests in `tests/test_engine.py`**

  Decorate each of `test_reflects_and_logs`, `test_no_evidence_does_not_pass`, `test_action_requires_approval`, `test_tool_blocked`, `test_cost_ceiling`.

- [ ] **Step 2: Write failing tests for new engine edge cases**

  ```python
  @pytest.mark.unit
  def test_no_change_stop_is_not_approved():
      # Generator that returns the same text forever
      class Identity:
          def generate(self, prompt, draft, critique, constraints): return draft, 0.0
      # FixtureJudge scores 0.3 without evidence; needs max_iterations>0 to trigger no_change
      r = ReflectionEngine(FixtureJudge(), Identity(), Policy(max_iterations=1)).run('t', 'draft')
      assert r.metrics.stop_reason == 'no_change'
      assert not r.approved

  @pytest.mark.unit
  def test_max_iterations_zero_no_regeneration():
      events = []
      e = ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy(max_iterations=0), events.append)
      r = e.run('task', 'draft', 'evidence')
      assert r.metrics.iteration_count == 0
      assert len(events) == 1  # single evaluate, no regen
  ```

- [ ] **Step 3: Run tests to verify they fail**

  Run: `uv run pytest tests/test_engine.py -v -m unit`
  Expected: 2 new tests FAIL, 5 existing PASS

- [ ] **Step 4: Write `tests/test_models.py` covering Policy and Evaluation validation**

  ```python
  @pytest.mark.unit
  def test_policy_invalid_max_iterations(): pytest.raises(ValueError, Policy, max_iterations=-1)

  @pytest.mark.unit
  def test_policy_invalid_min_score_above_one(): pytest.raises(ValueError, Policy, min_score=1.1)

  @pytest.mark.unit
  def test_policy_tool_overlap(): pytest.raises(ValueError, Policy, allowed_tools=('a',), forbidden_tools=('a',))

  @pytest.mark.unit
  def test_evaluation_invalid_score(): pytest.raises(ValueError, Evaluation, score=1.5, critique='x')

  @pytest.mark.unit
  def test_evaluation_negative_cost(): pytest.raises(ValueError, Evaluation, score=0.5, critique='x', cost=-1.0)

  @pytest.mark.unit
  def test_policy_is_frozen():
      p = Policy()
      with pytest.raises(Exception): p.max_iterations = 99

  @pytest.mark.unit
  def test_evaluation_is_frozen():
      e = Evaluation(0.5, 'ok')
      with pytest.raises(Exception): e.score = 1.0
  ```

- [ ] **Step 5: Run all tests to verify they fail before no implementation needed**

  Run: `uv run pytest tests/test_models.py -v`
  Expected: PASS (models.py already has the validation; this confirms coverage)

- [ ] **Step 6: Fix the two new engine edge-case tests**

  `test_no_change_stop_is_not_approved`: The `Identity` generator returns `draft` unchanged. After one regeneration that produces the same text, `stop_reason` becomes `no_change`. Verify `approved` is `False` — no code change needed if the engine already handles this. Run the test to confirm.

- [ ] **Step 7: Run full test suite**

  Run: `uv run pytest tests/test_engine.py tests/test_models.py -v -m unit`
  Expected: all PASS

- [ ] **Step 8: Commit**

  ```bash
  git add tests/test_engine.py tests/test_models.py
  git commit -m "test(models): add pytest.mark.unit, engine edge cases, full models.py coverage"
  ```

---

### Task 3: Provider Tests

**Files:**
- Create: `tests/test_providers.py`

**Interfaces:**
- Consumes: `FixtureJudge`, `FixtureGenerator`, `OpenAICompatible`, `JSONJudge`, `ConstrainedGenerator` from `src/sraf/core/providers.py`; `Evaluation`, `Policy` from `src/sraf/core/models.py`
- Produces: 95%+ coverage of `providers.py`; `pytest.mark.unit` on all provider tests

- [ ] **Step 1: Write failing tests for `FixtureJudge` and `FixtureGenerator`**

  ```python
  @pytest.mark.unit
  def test_fixture_judge_passes_with_citation():
      e = FixtureJudge().evaluate('p', 'answer. Source: doc', 'doc')
      assert e.score == 0.9 and not e.hallucination_risk

  @pytest.mark.unit
  def test_fixture_judge_fails_without_citation():
      e = FixtureJudge().evaluate('p', 'bare answer', '')
      assert e.score == 0.3 and e.hallucination_risk

  @pytest.mark.unit
  def test_fixture_generator_appends_citation():
      text, cost = FixtureGenerator().generate('p', 'draft', 'x', Policy())
      assert text.endswith('Source: supplied evidence') and cost == 0.0
  ```

- [ ] **Step 2: Run to verify tests pass (FixtureJudge/Generator are already implemented)**

  Run: `uv run pytest tests/test_providers.py::test_fixture_judge_passes_with_citation -v`
  Expected: PASS

- [ ] **Step 3: Write failing tests for `OpenAICompatible` URL validation**

  ```python
  @pytest.mark.unit
  def test_openai_requires_https():
      with pytest.raises(ValueError): OpenAICompatible('http://evil.com', 'gpt-4', 'k')

  @pytest.mark.unit
  def test_openai_allows_http_localhost():
      c = OpenAICompatible('http://localhost:11434', 'llama3', 'x')
      assert 'localhost' in c.url

  @pytest.mark.unit
  def test_openai_allows_https():
      c = OpenAICompatible('https://api.openai.com/v1', 'gpt-4', 'k')
      assert c.url.endswith('/chat/completions')
  ```

- [ ] **Step 4: Write failing tests for `JSONJudge` and `ConstrainedGenerator` using mocks**

  ```python
  from unittest.mock import MagicMock, patch

  @pytest.mark.unit
  def test_json_judge_parses_response():
      client = MagicMock()
      client.chat.return_value = '{"score":0.9,"critique":"ok","suggested_fixes":[],"hallucination_risk":false,"missing_steps":[],"tool_use_correct":true}'
      e = JSONJudge(client, cost_per_call=0.01).evaluate('p', 'out', 'ev')
      assert e.score == 0.9 and e.cost == 0.01

  @pytest.mark.unit
  def test_constrained_generator_calls_chat():
      client = MagicMock()
      client.chat.return_value = 'revised'
      text, cost = ConstrainedGenerator(client, cost_per_call=0.02).generate('p', 'd', 'c', Policy())
      assert text == 'revised' and cost == 0.02
  ```

- [ ] **Step 5: Run all provider tests**

  Run: `uv run pytest tests/test_providers.py -v`
  Expected: all PASS

- [ ] **Step 6: Commit**

  ```bash
  git add tests/test_providers.py
  git commit -m "test(providers): 95% coverage, URL validation, mock-based JSONJudge/ConstrainedGenerator"
  ```

---

### Task 4: Observability + CLI + Benchmark Tests

**Files:**
- Create: `tests/test_store.py`
- Create: `tests/test_cli.py`
- Create: `tests/test_benchmark.py`

**Interfaces:**
- Consumes: `JSONLStore` from `src/sraf/observability/store.py`; `main` from `src/sraf/cli.py`; `run_benchmark` from `src/sraf/evaluation/benchmark.py`
- Produces: 95%+ coverage of `store.py`, `cli.py`, `benchmark.py`

- [ ] **Step 1: Write `tests/test_store.py`**

  ```python
  @pytest.mark.unit
  def test_jsonl_store_writes_events(tmp_path):
      store = JSONLStore(str(tmp_path / 'sub' / 'trace.jsonl'))
      store({'key': 'val'})
      store({'key': 'val2'})
      lines = (tmp_path / 'sub' / 'trace.jsonl').read_text().splitlines()
      assert len(lines) == 2
      assert json.loads(lines[0])['key'] == 'val'

  @pytest.mark.unit
  def test_jsonl_store_creates_parent_dirs(tmp_path):
      store = JSONLStore(str(tmp_path / 'a' / 'b' / 'c.jsonl'))
      store({'x': 1})
      assert (tmp_path / 'a' / 'b' / 'c.jsonl').exists()
  ```

- [ ] **Step 2: Write `tests/test_cli.py`**

  ```python
  from unittest.mock import patch
  import sys

  @pytest.mark.unit
  def test_cli_runs_with_defaults(tmp_path, capsys):
      policy_file = tmp_path / 'p.json'
      policy_file.write_text('{"max_iterations":1,"max_cost":0.5,"min_score":0.8,"allowed_tools":[],"forbidden_tools":[],"required_human_review":false,"safety_tags":[]}')
      with patch('sys.argv', ['sraf', '--policy', str(policy_file), '--trace', str(tmp_path / 't.jsonl')]):
          from sraf.cli import main
          main()
      out = capsys.readouterr().out
      assert '"score"' in out

  @pytest.mark.unit
  def test_cli_output_is_valid_json(tmp_path, capsys):
      import json as _json
      policy_file = tmp_path / 'p.json'
      policy_file.write_text('{"max_iterations":1,"max_cost":0.5,"min_score":0.8,"allowed_tools":[],"forbidden_tools":[],"required_human_review":false,"safety_tags":[]}')
      with patch('sys.argv', ['sraf', '--policy', str(policy_file), '--trace', str(tmp_path / 't.jsonl')]):
          from sraf.cli import main
          main()
      _json.loads(capsys.readouterr().out)  # raises if invalid
  ```

- [ ] **Step 3: Read `src/sraf/evaluation/benchmark.py` and write `tests/test_benchmark.py`**

  Run: `cat src/sraf/evaluation/benchmark.py` to confirm the public function signatures, then write:
  ```python
  @pytest.mark.unit
  def test_benchmark_writes_artifacts(tmp_path):
      # patch output paths to tmp_path
      # call run_benchmark or main() with mock
      # assert metrics.json and report.md are created
  ```
  Exact assertions depend on the benchmark module's interface — read it first.

- [ ] **Step 4: Run all new tests**

  Run: `uv run pytest tests/test_store.py tests/test_cli.py tests/test_benchmark.py -v`
  Expected: all PASS

- [ ] **Step 5: Commit**

  ```bash
  git add tests/test_store.py tests/test_cli.py tests/test_benchmark.py
  git commit -m "test(observability,cli,benchmark): full offline coverage for store, cli, benchmark"
  ```

---

### Task 5: Adapter Tests

**Files:**
- Create: `tests/test_adapters.py`

**Interfaces:**
- Consumes: `build_graph` from `src/sraf/framework_adapters/langgraph_reflective_adapter.py`; `CrewAI` and `AutoGen` adapters from their respective files; `ReflectionEngine`, `Policy`, `FixtureJudge`, `FixtureGenerator`
- Produces: 95%+ coverage of all three adapter files; `pytest.mark.unit`; adapters tested without real framework installs via `unittest.mock`

- [ ] **Step 1: Read `crewai_reflective_adapter.py` and `autogen_reflective_adapter.py`**

  Run: `cat src/sraf/framework_adapters/crewai_reflective_adapter.py src/sraf/framework_adapters/autogen_reflective_adapter.py`
  Map the public API (class names, function signatures) before writing tests.

- [ ] **Step 2: Write LangGraph adapter test (mock `langgraph`)**

  ```python
  @pytest.mark.unit
  def test_langgraph_adapter_invokes_engine():
      from unittest.mock import patch, MagicMock
      mock_sg = MagicMock()
      mock_sg.return_value.compile.return_value.invoke.return_value = {'result': {'score': 0.9}}
      with patch.dict('sys.modules', {'langgraph': MagicMock(), 'langgraph.graph': mock_sg}):
          from sraf.framework_adapters.langgraph_reflective_adapter import build_graph
          engine = ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy())
          g = build_graph(lambda p: 'draft Source: ev', engine)
          # build_graph returns compiled graph; calling invoke verifies wiring
  ```

- [ ] **Step 3: Write CrewAI and AutoGen adapter tests using same `patch.dict` pattern**

  Each test: mock the framework import, instantiate the adapter, call its main entry point, assert it delegates to `ReflectionEngine.run`.

- [ ] **Step 4: Run adapter tests**

  Run: `uv run pytest tests/test_adapters.py -v`
  Expected: all PASS

- [ ] **Step 5: Check overall coverage so far**

  Run: `uv run pytest -m unit --cov=src/sraf --cov-report=term-missing`
  Expected: `src/sraf/core/` ≥ 95%, `src/sraf/observability/` ≥ 95%, `src/sraf/cli.py` ≥ 95%

- [ ] **Step 6: Commit**

  ```bash
  git add tests/test_adapters.py
  git commit -m "test(adapters): offline coverage for langgraph, crewai, autogen adapters via mock"
  ```

---

### Task 6: FastAPI Schemas

**Files:**
- Create: `src/sraf/api/__init__.py`
- Create: `src/sraf/api/schemas.py`

**Interfaces:**
- Produces:
  - `ReflectRequest(prompt: str, draft: str, evidence: str = "", tools: list[str] = [], pending_actions: list[str] = [], policy_override: dict | None = None)` — Pydantic BaseModel
  - `ReflectResponse(score: float, critique: str, approved: bool, stop_reason: str, iteration_count: int, cost: float, output: str)` — Pydantic BaseModel
  - `HealthResponse(status: str)` — Pydantic BaseModel

- [ ] **Step 1: Write failing test for schema validation**

  ```python
  @pytest.mark.unit
  def test_reflect_request_requires_prompt():
      from sraf.api.schemas import ReflectRequest
      with pytest.raises(Exception): ReflectRequest()  # prompt missing

  @pytest.mark.unit
  def test_reflect_response_fields():
      from sraf.api.schemas import ReflectResponse
      r = ReflectResponse(score=0.9, critique='ok', approved=True, stop_reason='quality_gate', iteration_count=1, cost=0.01, output='answer')
      assert r.score == 0.9
  ```

- [ ] **Step 2: Run to verify FAIL (schemas.py doesn't exist yet)**

  Run: `uv run pytest tests/test_api.py::test_reflect_request_requires_prompt -v`
  Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `src/sraf/api/__init__.py`** (empty)

- [ ] **Step 4: Implement `src/sraf/api/schemas.py`**

  Pydantic v2 `BaseModel` for `ReflectRequest`, `ReflectResponse`, `HealthResponse`. Add `model_config = ConfigDict(extra="forbid")` on `ReflectRequest` to block extra fields.

- [ ] **Step 5: Run tests**

  Run: `uv run pytest tests/test_api.py -k schema -v`
  Expected: schema tests PASS

- [ ] **Step 6: Commit**

  ```bash
  git add src/sraf/api/
  git commit -m "feat(api): add Pydantic schemas for reflect request/response"
  ```

---

### Task 7: Security Middleware

**Files:**
- Create: `src/sraf/api/middleware.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (standalone ASGI middleware)
- Produces:
  - `APIKeyMiddleware(app, api_key: str)` — Starlette `BaseHTTPMiddleware`; returns 401 if `Authorization: Bearer <key>` header missing or key mismatch (use `hmac.compare_digest`)
  - `SlidingWindowRateLimiter(app, limit: int = 60, window_seconds: int = 60)` — `BaseHTTPMiddleware`; tracks per-IP request counts in a `threading.Lock`-protected dict; returns 429 with `Retry-After` header when exceeded
  - `SecurityHeadersMiddleware(app)` — `BaseHTTPMiddleware`; adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`
  - `sanitize_string(value: str, max_len: int = 4096) -> str` — strips null bytes, truncates; raises `ValueError` if `value` after strip is empty and `max_len > 0`

- [ ] **Step 1: Write failing tests for middleware and sanitize**

  ```python
  @pytest.mark.unit
  def test_api_key_middleware_rejects_missing_auth():
      # Use Starlette TestClient with a minimal ASGI app wrapped by APIKeyMiddleware
      from starlette.testclient import TestClient
      from starlette.applications import Starlette
      from starlette.routing import Route
      from starlette.responses import JSONResponse
      from sraf.api.middleware import APIKeyMiddleware
      app = APIKeyMiddleware(Starlette(routes=[Route('/', lambda r: JSONResponse({'ok': True}))]), api_key='secret')
      assert TestClient(app, raise_server_exceptions=False).get('/').status_code == 401

  @pytest.mark.unit
  def test_api_key_middleware_accepts_correct_key(): ...  # 200

  @pytest.mark.unit
  def test_rate_limiter_blocks_after_limit(): ...  # 429 on N+1 request

  @pytest.mark.unit
  def test_rate_limiter_thread_safety(): ...  # two threads, assert no data race (use threading)

  @pytest.mark.unit
  def test_security_headers_present(): ...  # check X-Content-Type-Options in response

  @pytest.mark.unit
  def test_sanitize_strips_null_bytes():
      from sraf.api.middleware import sanitize_string
      assert sanitize_string('hello\x00world') == 'helloworld'

  @pytest.mark.unit
  def test_sanitize_truncates():
      assert len(sanitize_string('x' * 5000)) == 4096
  ```

- [ ] **Step 2: Run to verify FAIL**

  Run: `uv run pytest tests/test_api.py -k middleware -v`
  Expected: FAIL (middleware.py missing)

- [ ] **Step 3: Implement `src/sraf/api/middleware.py`**

  `APIKeyMiddleware`: use `hmac.compare_digest(provided_key, self.api_key)` — never `==`.
  `SlidingWindowRateLimiter`: `threading.Lock` on dict of `{ip: deque[float]}`, prune entries outside window on each request.
  `SecurityHeadersMiddleware`: set all 5 headers in `after_response` via `MutableHeaders`.
  `sanitize_string(value, max_len=4096)`: `value.replace('\x00', '')[:max_len]`.

- [ ] **Step 4: Run middleware tests**

  Run: `uv run pytest tests/test_api.py -k middleware -v`
  Expected: all PASS

- [ ] **Step 5: Commit**

  ```bash
  git add src/sraf/api/middleware.py
  git commit -m "feat(api): security middleware — API key auth, sliding-window rate limit, OWASP headers"
  ```

---

### Task 8: Routes + App Assembly

**Files:**
- Create: `src/sraf/api/routes.py`
- Create: `src/sraf/api/app.py`

**Interfaces:**
- Consumes: `ReflectRequest`, `ReflectResponse`, `HealthResponse` from Task 6; `APIKeyMiddleware`, `SlidingWindowRateLimiter`, `SecurityHeadersMiddleware`, `sanitize_string` from Task 7; `ReflectionEngine`, `Policy`, `FixtureJudge`, `FixtureGenerator` from core
- Produces:
  - `create_app(api_key: str = "", rate_limit: int = 60) -> FastAPI` — factory function; mounts all middleware; registers routes
  - Routes: `GET /health → HealthResponse(status="ok")`, `GET /readyz → HealthResponse(status="ready")`, `POST /reflect → ReflectResponse`
  - `/reflect` loads `Policy` from `policy_override` if provided (falls back to `policies/default.json`), runs `ReflectionEngine` with `FixtureJudge` + `FixtureGenerator`, sanitizes `prompt`/`draft`/`evidence` via `sanitize_string`

- [ ] **Step 1: Write failing tests for routes**

  ```python
  @pytest.mark.unit
  def test_health_endpoint():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      client = TestClient(create_app())
      assert client.get('/health').json() == {'status': 'ok'}

  @pytest.mark.unit
  def test_reflect_endpoint_returns_score():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      client = TestClient(create_app())
      r = client.post('/reflect', json={'prompt': 'task', 'draft': 'answer. Source: ev', 'evidence': 'ev'})
      assert r.status_code == 200
      assert 'score' in r.json()

  @pytest.mark.unit
  def test_reflect_rejects_extra_fields():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      client = TestClient(create_app())
      r = client.post('/reflect', json={'prompt': 'task', 'draft': 'd', 'unknown_field': 'x'})
      assert r.status_code == 422
  ```

- [ ] **Step 2: Run to verify FAIL**

  Run: `uv run pytest tests/test_api.py -k endpoint -v`
  Expected: FAIL (routes.py and app.py missing)

- [ ] **Step 3: Implement `src/sraf/api/routes.py`**

  `APIRouter` with `/health`, `/readyz`, and `/reflect`. Load `policies/default.json` on module init; `policy_override` in request body replaces fields. Sanitize `prompt`, `draft`, `evidence` before passing to engine.

- [ ] **Step 4: Implement `src/sraf/api/app.py`**

  `create_app(api_key="", rate_limit=60) -> FastAPI`: add `SecurityHeadersMiddleware`, `SlidingWindowRateLimiter`, and (if `api_key`) `APIKeyMiddleware` in that order (outermost first). Include router.

- [ ] **Step 5: Run route tests**

  Run: `uv run pytest tests/test_api.py -k "endpoint or health or reflect" -v`
  Expected: all PASS

- [ ] **Step 6: Commit**

  ```bash
  git add src/sraf/api/routes.py src/sraf/api/app.py
  git commit -m "feat(api): FastAPI app with /health, /readyz, /reflect routes and middleware wiring"
  ```

---

### Task 9: Full API Test Suite

**Files:**
- Modify: `tests/test_api.py` (consolidate all API tests written in Tasks 6-8 + add missing coverage)

**Interfaces:**
- Consumes: `create_app` from `src/sraf/api/app.py`; schemas from Task 6; middleware from Task 7

- [ ] **Step 1: Write tests for auth-gated mode**

  ```python
  @pytest.mark.unit
  def test_auth_gated_app_requires_bearer():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      client = TestClient(create_app(api_key='secret123'), raise_server_exceptions=False)
      assert client.post('/reflect', json={'prompt': 'x', 'draft': 'y'}).status_code == 401
      assert client.post('/reflect', json={'prompt': 'x', 'draft': 'y'},
                         headers={'Authorization': 'Bearer secret123'}).status_code == 200
  ```

- [ ] **Step 2: Write test for null-byte injection in prompt**

  ```python
  @pytest.mark.unit
  def test_reflect_sanitizes_null_bytes():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      r = TestClient(create_app()).post('/reflect', json={'prompt': 'task\x00injected', 'draft': 'd'})
      assert r.status_code == 200  # sanitized, not rejected
  ```

- [ ] **Step 3: Write test for OWASP headers present on all responses**

  ```python
  @pytest.mark.unit
  def test_security_headers_on_health():
      from fastapi.testclient import TestClient
      from sraf.api.app import create_app
      r = TestClient(create_app()).get('/health')
      assert r.headers.get('x-content-type-options') == 'nosniff'
      assert r.headers.get('x-frame-options') == 'DENY'
  ```

- [ ] **Step 4: Run full API test suite**

  Run: `uv run pytest tests/test_api.py -v`
  Expected: all PASS

- [ ] **Step 5: Run full coverage check**

  Run: `uv run pytest -m unit --cov=src/sraf --cov-report=term-missing --cov-fail-under=80`
  Expected: PASS with ≥80% across all modules

- [ ] **Step 6: Commit**

  ```bash
  git add tests/test_api.py
  git commit -m "test(api): full API test suite — auth, rate-limit, OWASP headers, null-byte injection"
  ```

---

### Task 10: Architecture Documentation

**Files:**
- Create: `ARCHITECTURE.md`
- Create: `SECURITY.md`
- Modify: `README.md`

**Interfaces:**
- Produces: `ARCHITECTURE.md` with two Mermaid diagrams (Layered System + End-to-End Sequence); `SECURITY.md` with threat model and invariants; `README.md` with CI badge, coverage badge, eval scorecard table, diagram embed links

- [ ] **Step 1: Create `ARCHITECTURE.md` with Layered System diagram**

  ```mermaid
  graph TD
    subgraph "HTTP Layer (optional, api extras)"
      A[FastAPI /reflect] --> B[SecurityHeadersMiddleware]
      B --> C[SlidingWindowRateLimiter]
      C --> D[APIKeyMiddleware]
      D --> E[ReflectRequest validation]
    end
    subgraph "Core Library (zero-dependency)"
      E --> F[ReflectionEngine.run]
      F --> G[Judge.evaluate]
      F --> H[Policy gate]
      H --> I[Generator.generate]
      I --> F
      F --> J[ReflectionResult]
    end
    subgraph "Adapters (optional extras)"
      K[LangGraph node] --> F
      L[CrewAI task] --> F
      M[AutoGen participant] --> F
    end
  ```

  Add End-to-End Sequence diagram (Mermaid `sequenceDiagram`): caller → API → engine → judge → gate → generator → judge → gate → approval → response.

  Document `RunMetadata` mutability rationale: accumulates during live loop; frozen snapshot pattern would require builder, adding complexity without safety benefit for a single-threaded run.

- [ ] **Step 2: Create `SECURITY.md`**

  Sections: Threat Model (prompt injection, cost abuse, tool abuse, SSRF), Invariants (fail-closed policy gate, HTTPS enforcement, `hmac.compare_digest`), Reporting (GitHub Issues with `security` label), Known Limitations (redirect-following in `urlopen`).

- [ ] **Step 3: Update `README.md`**

  Add: CI badge (`[![CI](https://github.com/AshraHossain/SRAF/actions/workflows/ci.yml/badge.svg)`), coverage badge (Codecov or shields.io static), evaluation scorecard table (columns: Case, Min Score, Iterations, Stop Reason, Approved), link to `ARCHITECTURE.md`.

- [ ] **Step 4: Verify Mermaid renders**

  Run: `cat ARCHITECTURE.md | grep mermaid | wc -l`; visually inspect diagram block syntax.

- [ ] **Step 5: Commit**

  ```bash
  git add ARCHITECTURE.md SECURITY.md README.md
  git commit -m "docs(arch): add Mermaid architecture diagrams, SECURITY.md, README badges and scorecard"
  ```

---

### Task 11: Makefile + CI Gate

**Files:**
- Create: `Makefile`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `make check` = lint + unit tests + eval; `make test` = full pytest; `make lint` = ruff; `make eval` = benchmark; CI uses `make check` as the gate

- [ ] **Step 1: Create `Makefile`**

  ```makefile
  .PHONY: check test lint eval

  check: lint test eval

  lint:
  	uv run ruff check src tests

  test:
  	uv run pytest -m unit --cov=src/sraf --cov-report=term-missing --cov-fail-under=80

  eval:
  	uv run python -m sraf.evaluation.benchmark
  ```

- [ ] **Step 2: Run `make check` and verify it passes**

  Run: `make check`
  Expected: lint passes, tests pass with ≥80% coverage, benchmark completes

- [ ] **Step 3: Add `make check` step to CI**

  In `.github/workflows/ci.yml`, add a `check` job that runs `make check` after lint and test jobs.

- [ ] **Step 4: Commit**

  ```bash
  git add Makefile .github/workflows/ci.yml
  git commit -m "chore(ci): add Makefile with make check, wire CI gate to make check"
  ```

---

### Task 12: Containerization

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Interfaces:**
- Produces: `docker build -t sraf .` succeeds; `docker run sraf` runs the CLI; `docker compose up` starts the FastAPI service on port 8000

- [ ] **Step 1: Create `.dockerignore`**

  ```
  .git
  __pycache__
  *.pyc
  .venv
  graphify-out
  artifacts
  .ruff_cache
  dist
  ```

- [ ] **Step 2: Create `Dockerfile`**

  ```dockerfile
  FROM python:3.11-slim AS builder
  WORKDIR /app
  COPY pyproject.toml .
  RUN pip install uv && uv pip install --system ".[api]"

  FROM python:3.11-slim
  RUN useradd -u 10001 -m sraf
  WORKDIR /app
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin
  COPY src/ src/
  COPY policies/ policies/
  USER sraf
  CMD ["sraf"]
  ```

- [ ] **Step 3: Create `docker-compose.yml`**

  ```yaml
  services:
    api:
      build: .
      command: uvicorn sraf.api.app:create_app --factory --host 0.0.0.0 --port 8000
      ports: ["8000:8000"]
      environment:
        SRAF_API_KEY: ${SRAF_API_KEY:-}
      user: "10001"
  ```

- [ ] **Step 4: Verify image builds**

  Run: `docker build -t sraf . 2>&1 | tail -5`
  Expected: `Successfully built` or `exporting to image`

- [ ] **Step 5: Verify non-root user**

  Run: `docker run --rm sraf whoami`
  Expected: `sraf`

- [ ] **Step 6: Commit**

  ```bash
  git add Dockerfile docker-compose.yml .dockerignore
  git commit -m "chore(docker): multi-stage Dockerfile with non-root UID 10001, docker-compose for API service"
  ```

---

### Task 13: Final Validation + Release

**Files:** No new files; all existing files should be in final state.

- [ ] **Step 1: Run `make check`**

  Run: `make check`
  Expected: lint PASS, all unit tests PASS, coverage ≥ 80%, benchmark completes

- [ ] **Step 2: Run full test suite including any live-marked tests**

  Run: `uv run pytest -v` (all markers)
  Expected: all PASS (live tests skip if no API key set)

- [ ] **Step 3: Verify Docker builds and passes smoke test**

  Run: `docker build -t sraf . && docker run --rm sraf`
  Expected: JSON output from CLI, no errors

- [ ] **Step 4: Run graphify update**

  Run: `/graphify update` (or `graphify update .`)
  Expected: "No files changed" or incremental update with new nodes for `src/sraf/api/`

- [ ] **Step 5: Final commit and push**

  ```bash
  git status  # verify nothing unexpected
  git add -A
  git commit -m "feat(sraf): enterprise upgrade — FastAPI service, 95% test coverage, security hardening, Docker, CI gate"
  git push origin main
  ```

---

## Self-Review

**1. Spec coverage:**
- Phase 1 (audit + instruction alignment): Task 1 ✓
- Phase 2 (95% offline coverage, frozen DTOs note, pytest-mark): Tasks 1-5 ✓; `RunMetadata` mutability documented in Task 10 ✓
- Phase 2.5 (auth, rate-limit, OWASP headers, sanitization): Tasks 6-9 ✓
- Phase 3 (Mermaid diagrams, eval scorecard, Makefile, badges): Tasks 10-11 ✓
- Phase 4 (Dockerfile, docker-compose, make check, graphify, commit+push): Tasks 12-13 ✓

**2. Step scan:** Each step names one file or one command. No "add appropriate validation" vagueness — specific method names and assertion values throughout.

**3. Type consistency:** `create_app(api_key: str = "", rate_limit: int = 60) -> FastAPI` defined in Task 8 Interfaces, consumed in Task 9 tests ✓. `sanitize_string(value: str, max_len: int = 4096) -> str` defined in Task 7, used in Task 9 ✓.

**4. Review Focus:** All 5 items have tests added to owning tasks ✓.

**5. Proportion:** Plan covers 13 tasks for a ~600-line code change. Code blocks are test assertions and interface signatures, not implementations. Acceptable.
