from dataclasses import dataclass, field
from math import isfinite
from numbers import Real
from typing import Any


_FIELD_OUTCOMES = {
    "exact",
    "partial",
    "conflict",
    "missing",
    "not_comparable",
}

_DECISIONS = {"matched", "review_required", "no_match"}

_DECISION_RULES = {
    "high_confidence_threshold",
    "review_threshold",
    "ambiguity_margin",
    "no_candidate",
    "missing_matching_value",
    "no_exact_match",
    "exact_composite_key_match",
    "duplicate_source_key",
    "duplicate_target_key",
    "target_already_assigned",
    "confidence_below_auto_match_threshold",
    "confidence_below_review_threshold",
}


def _validate_score(name: str, value: float | None) -> None:
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number between 0 and 1.")

    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite number between 0 and 1.")


def _validate_finite(name: str, value: float | None) -> None:
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be finite.")

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")


@dataclass(frozen=True)
class MatchFieldEvidence:
    """Structured evidence for one configured field comparison."""

    field: str
    outcome: str
    score: float | None = None
    comparable: bool = True
    contribution: float | None = None
    explanation_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.field, str) or not self.field.strip():
            raise ValueError("field must be a non-empty string.")

        if self.outcome not in _FIELD_OUTCOMES:
            raise ValueError(
                "outcome must be one of: "
                + ", ".join(sorted(_FIELD_OUTCOMES))
                + "."
            )

        if not isinstance(self.comparable, bool):
            raise ValueError("comparable must be a boolean.")

        if self.outcome in {"missing", "not_comparable"}:
            if self.comparable:
                raise ValueError(
                    "Missing or non-comparable evidence must set "
                    "comparable to False."
                )
            if self.score is not None or self.contribution is not None:
                raise ValueError(
                    "Missing or non-comparable evidence cannot include "
                    "a score or contribution."
                )
        elif not self.comparable:
            raise ValueError(
                "Populated comparison outcomes must be comparable."
            )

        _validate_score("score", self.score)
        _validate_finite("contribution", self.contribution)

        if self.explanation_code is not None and (
            not isinstance(self.explanation_code, str)
            or not self.explanation_code.strip()
        ):
            raise ValueError(
                "explanation_code must be a non-empty string when provided."
            )


@dataclass(frozen=True)
class MatchDecisionEvidence:
    """Structured evidence for the final match decision."""

    decision: str
    rule: str | None = None
    threshold: float | None = None
    best_score: float | None = None
    second_best_score: float | None = None
    score_gap: float | None = None
    comparable_field_count: int = 0
    summary: str | None = None

    def __post_init__(self) -> None:
        if self.decision not in _DECISIONS:
            raise ValueError(
                "decision must be one of: "
                + ", ".join(sorted(_DECISIONS))
                + "."
            )

        if self.rule is not None and self.rule not in _DECISION_RULES:
            raise ValueError(
                "rule must be a recognized matching decision rule."
            )

        _validate_score("threshold", self.threshold)
        _validate_score("best_score", self.best_score)
        _validate_score("second_best_score", self.second_best_score)
        _validate_score("score_gap", self.score_gap)

        if (
            self.best_score is not None
            and self.second_best_score is not None
            and self.second_best_score > self.best_score
        ):
            raise ValueError(
                "second_best_score cannot exceed best_score."
            )

        if (
            self.best_score is not None
            and self.second_best_score is not None
            and self.score_gap is not None
            and abs(
                self.score_gap
                - (self.best_score - self.second_best_score)
            )
            > 1e-9
        ):
            raise ValueError(
                "score_gap must equal best_score minus second_best_score."
            )

        if (
            isinstance(self.comparable_field_count, bool)
            or not isinstance(self.comparable_field_count, int)
            or self.comparable_field_count < 0
        ):
            raise ValueError(
                "comparable_field_count must be a non-negative integer."
            )

        if self.summary is not None and not isinstance(self.summary, str):
            raise ValueError("summary must be a string when provided.")


@dataclass(frozen=True)
class MatchExplanation:
    """Structured explanation for one entity-matching result."""

    field_evidence: tuple[MatchFieldEvidence, ...]
    decision: MatchDecisionEvidence


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
    explanation: MatchExplanation | None = None
