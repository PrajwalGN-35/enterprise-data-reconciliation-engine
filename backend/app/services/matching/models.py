from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MatchCandidate:
    source_index: int
    target_index: int
    source_value: Any
    target_value: Any
    field: str


@dataclass(frozen=True)
class SimilarityResult:
    score: float
    method: str


@dataclass
class EntityMatch:
    source_index: int
    target_index: int | None
    status: str
    confidence: float
    method: str
    field_scores: dict[str, float] = field(default_factory=dict)
    reason: str | None = None
