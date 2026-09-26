from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import uuid4

from .models import Evaluation, Policy, ReflectionResult, RunMetadata, now


class Judge(Protocol):
    def evaluate(self, prompt: str, output: str, evidence: str) -> Evaluation: ...

class Generator(Protocol):
    def generate(self, prompt: str, draft: str, critique: str, constraints: Policy) -> tuple[str, float]: ...

class ReflectionEngine:
    def __init__(self, judge: Judge, generator: Generator, policy: Policy,
                 sink: Callable[[dict], None] | None = None):
        self.judge, self.generator, self.policy, self.sink = judge, generator, policy, sink

    def evaluate_output(self, prompt: str, output: str, evidence: str = "") -> Evaluation:
        return self.judge.evaluate(prompt, output, evidence)

    def critique_reasoning(self, evaluation: Evaluation) -> str:
        return evaluation.critique

    def enforce_policies(self, tools: tuple[str, ...], estimated_cost: float) -> None:
        if estimated_cost > self.policy.max_cost:
            raise ValueError("Cost ceiling exceeded")
        if set(tools) & set(self.policy.forbidden_tools):
            raise ValueError("Forbidden tool")
        if self.policy.allowed_tools and not set(tools) <= set(self.policy.allowed_tools):
            raise ValueError("Tool not allowlisted")

    def regenerate_with_constraints(self, prompt: str, output: str, critique: str) -> tuple[str, float]:
        return self.generator.generate(prompt, output, critique, self.policy)

    @staticmethod
    def track_improvement(first: float, last: float) -> float:
        return round(last - first, 4)

    def run(self, prompt: str, draft: str, evidence: str = "", tools: tuple[str, ...] = (),
            pending_actions: list[str] | None = None,
            approval: Callable[[list[str]], bool] | None = None) -> ReflectionResult:
        self.enforce_policies(tools, 0)
        meta = RunMetadata(trace_id=uuid4().hex)
        history: list[dict] = []
        current = draft
        regenerated: str | None = None
        first: float | None = None
        actions = pending_actions or []
        try:
            for iteration in range(self.policy.max_iterations + 1):
                evaluation = self.evaluate_output(prompt, current, evidence)
                meta.cost += evaluation.cost
                history.append({"iteration": iteration, "score": evaluation.score,
                                "cost": evaluation.cost, "critique": evaluation.critique,
                                "output": current, "timestamp": now()})
                if self.sink:
                    self.sink({"trace_id": meta.trace_id, **history[-1]})
                if first is None:
                    first = evaluation.score
                if meta.cost > self.policy.max_cost:
                    meta.stop_reason = "cost_ceiling"
                    break
                if evaluation.score >= self.policy.min_score and not evaluation.hallucination_risk and evaluation.tool_use_correct:
                    meta.stop_reason = "quality_gate"
                    break
                if iteration == self.policy.max_iterations:
                    meta.stop_reason = "iteration_limit"
                    break
                previous = current
                candidate, generation_cost = self.regenerate_with_constraints(prompt, current, evaluation.critique)
                if generation_cost < 0:
                    raise ValueError("Negative generation cost")
                meta.cost += generation_cost
                if meta.cost > self.policy.max_cost:
                    meta.stop_reason = "cost_ceiling"
                    break
                current = candidate
                regenerated = candidate
                meta.iteration_count += 1
                if previous == candidate:
                    meta.stop_reason = "no_change"
                    break
            meta.improvement_delta = self.track_improvement(first or 0, evaluation.score)
            approved = meta.stop_reason == "quality_gate"
            if actions:
                approved = approved and (not self.policy.required_human_review or bool(approval and approval(actions)))
                if not approved and meta.stop_reason == "quality_gate":
                    meta.stop_reason = "human_review_required"
            return ReflectionResult(evaluation.score, evaluation.critique,
                                    list(evaluation.suggested_fixes), regenerated, current,
                                    meta, history, approved, actions)
        finally:
            meta.finished_at = now()
