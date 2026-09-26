from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def now() -> str:
    return datetime.now(UTC).isoformat()

@dataclass(frozen=True)
class Policy:
    max_iterations: int = 2
    max_cost: float = 0.10
    min_score: float = 0.8
    allowed_tools: tuple[str, ...] = ()
    forbidden_tools: tuple[str, ...] = ()
    required_human_review: bool = False
    safety_tags: tuple[str, ...] = ()
    def __post_init__(self) -> None:
        if self.max_iterations < 0 or self.max_cost < 0 or not 0 <= self.min_score <= 1:
            raise ValueError("Invalid policy bounds")
        if set(self.allowed_tools) & set(self.forbidden_tools):
            raise ValueError("Tools cannot be both allowed and forbidden")

@dataclass(frozen=True)
class Evaluation:
    score: float
    critique: str
    suggested_fixes: tuple[str, ...] = ()
    hallucination_risk: bool = False
    missing_steps: tuple[str, ...] = ()
    tool_use_correct: bool = True
    cost: float = 0.0
    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1 or self.cost < 0:
            raise ValueError("Invalid evaluation")

@dataclass
class RunMetadata:
    iteration_count: int = 0
    improvement_delta: float = 0.0
    cost: float = 0.0
    started_at: str = field(default_factory=now)
    finished_at: str | None = None
    stop_reason: str = ""
    trace_id: str = ""

@dataclass
class ReflectionResult:
    score: float
    critique: str
    suggested_fixes: list[str]
    regenerated_output: str | None
    output: str
    metrics: RunMetadata
    history: list[dict[str, Any]] = field(default_factory=list)
    approved: bool = False
    pending_actions: list[str] = field(default_factory=list)
