from dataclasses import asdict
import math

import pytest

from app.services.matching.models import (
    EntityMatch,
    MatchDecisionEvidence,
    MatchExplanation,
    MatchFieldEvidence,
)


@pytest.mark.parametrize("outcome", ["exact", "partial", "conflict"])
def test_populated_field_evidence_is_valid(outcome):
    evidence = MatchFieldEvidence(
        field="email",
        outcome=outcome,
        score=0.85 if outcome != "conflict" else 0.0,
        contribution=0.42,
        explanation_code=f"{outcome}_comparison",
    )

    assert evidence.outcome == outcome
    assert evidence.comparable is True


@pytest.mark.parametrize("outcome", ["missing", "not_comparable"])
def test_non_comparable_field_evidence_is_explicit(outcome):
    evidence = MatchFieldEvidence(
        field="phone",
        outcome=outcome,
        comparable=False,
    )

    assert evidence.score is None
    assert evidence.contribution is None


def test_invalid_field_outcome_is_rejected():
    with pytest.raises(ValueError, match="outcome"):
        MatchFieldEvidence("email", "unknown")


@pytest.mark.parametrize("score", [-0.01, 1.01, float("nan"), float("inf")])
def test_field_score_must_be_finite_and_bounded(score):
    with pytest.raises(ValueError, match="score"):
        MatchFieldEvidence("email", "partial", score=score)


@pytest.mark.parametrize("contribution", [float("nan"), float("inf")])
def test_field_contribution_must_be_finite(contribution):
    with pytest.raises(ValueError, match="contribution"):
        MatchFieldEvidence(
            "email",
            "partial",
            score=0.5,
            contribution=contribution,
        )


def test_missing_field_cannot_be_a_zero_score_conflict():
    with pytest.raises(ValueError, match="cannot include"):
        MatchFieldEvidence(
            "email",
            "missing",
            score=0.0,
            comparable=False,
        )


def test_decision_evidence_accepts_threshold_and_ambiguity_data():
    evidence = MatchDecisionEvidence(
        decision="review_required",
        rule="ambiguity_margin",
        threshold=0.90,
        best_score=0.88,
        second_best_score=0.84,
        score_gap=0.04,
        comparable_field_count=2,
        summary="Candidates are too close to select automatically.",
    )

    assert evidence.score_gap == 0.04
    assert evidence.comparable_field_count == 2


def test_decision_evidence_allows_missing_optional_values():
    evidence = MatchDecisionEvidence(
        decision="no_match",
        rule="no_candidate",
    )

    assert evidence.threshold is None
    assert evidence.second_best_score is None


@pytest.mark.parametrize(
    "value",
    [-0.01, 1.01, float("nan"), float("inf")],
)
def test_decision_scores_must_be_finite_and_bounded(value):
    with pytest.raises(ValueError):
        MatchDecisionEvidence(
            decision="matched",
            best_score=value,
        )


def test_invalid_decision_and_rule_are_rejected():
    with pytest.raises(ValueError, match="decision"):
        MatchDecisionEvidence("undecided")

    with pytest.raises(ValueError, match="rule"):
        MatchDecisionEvidence("matched", rule="invented_rule")


def test_score_gap_must_be_consistent_with_candidate_scores():
    with pytest.raises(ValueError, match="score_gap"):
        MatchDecisionEvidence(
            decision="review_required",
            best_score=0.9,
            second_best_score=0.8,
            score_gap=0.2,
        )

    with pytest.raises(ValueError, match="second_best_score"):
        MatchDecisionEvidence(
            decision="review_required",
            best_score=0.8,
            second_best_score=0.9,
        )


def test_explanation_serializes_nested_models():
    explanation = MatchExplanation(
        field_evidence=(
            MatchFieldEvidence("email", "exact", score=1.0),
            MatchFieldEvidence("phone", "missing", comparable=False),
        ),
        decision=MatchDecisionEvidence(
            decision="matched",
            rule="high_confidence_threshold",
            threshold=0.90,
            best_score=1.0,
            comparable_field_count=1,
        ),
    )

    serialized = asdict(explanation)

    assert serialized["field_evidence"][0]["outcome"] == "exact"
    assert serialized["field_evidence"][1]["comparable"] is False
    assert serialized["decision"]["best_score"] == 1.0


def test_entity_match_remains_backward_compatible_without_explanation():
    result = EntityMatch(
        source_index=0,
        target_index=1,
        status="matched",
        confidence=1.0,
        method="fuzzy",
    )

    assert result.field_scores == {}
    assert result.reason is None
    assert result.explanation is None


def test_entity_match_preserves_existing_fields_with_explanation():
    explanation = MatchExplanation(
        field_evidence=(
            MatchFieldEvidence("email", "partial", score=0.8),
        ),
        decision=MatchDecisionEvidence(
            decision="review_required",
            rule="review_threshold",
            threshold=0.75,
            best_score=0.8,
            comparable_field_count=1,
        ),
    )
    result = EntityMatch(
        source_index=0,
        target_index=1,
        status="review_required",
        confidence=0.8,
        method="fuzzy",
        field_scores={"email": 0.8},
        reason="confidence_below_auto_match_threshold",
        explanation=explanation,
    )

    serialized = asdict(result)

    assert serialized["source_index"] == 0
    assert serialized["target_index"] == 1
    assert serialized["status"] == "review_required"
    assert math.isclose(serialized["confidence"], 0.8)
    assert serialized["field_scores"] == {"email": 0.8}
    assert serialized["reason"] == "confidence_below_auto_match_threshold"
    assert serialized["explanation"]["decision"]["decision"] == (
        "review_required"
    )
