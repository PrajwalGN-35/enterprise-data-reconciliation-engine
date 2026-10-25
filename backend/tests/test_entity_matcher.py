import math
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest

from app.services.matching.entity_matcher import (
    match_entities,
)


def test_high_confidence_match():
    source = [
        {
            "name": "Prajwal G N",
            "email": "prajwal@gmail.com",
        }
    ]

    target = [
        {
            "name": "Prajwal G. N",
            "email": "PRAJWAL@GMAIL.COM",
        }
    ]

    results = match_entities(
        source,
        target,
        fields=["name", "email"],
    )

    assert len(results) == 1
    assert results[0].status == "matched"
    assert results[0].target_index == 0
    assert results[0].confidence >= 0.90


def test_fuzzy_match_explains_fields_and_aggregate_contributions():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        fields=["name", "email"],
    )[0]

    assert result.explanation is not None
    assert [item.outcome for item in result.explanation.field_evidence] == [
        "exact",
        "exact",
    ]
    assert all(
        item.contribution == 0.5
        for item in result.explanation.field_evidence
    )
    assert sum(
        item.contribution
        for item in result.explanation.field_evidence
        if item.contribution is not None
    ) == result.confidence
    assert result.explanation.decision.decision == "matched"
    assert result.explanation.decision.rule == "high_confidence_threshold"
    assert result.explanation.decision.threshold == 0.90


def test_partial_and_conflicting_fields_are_distinguished():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "Rahul K", "email": "zzzzzzzzzzzz"}],
        fields=["name", "email"],
    )[0]

    evidence_by_field = {
        item.field: item
        for item in result.explanation.field_evidence
    }

    assert evidence_by_field["name"].outcome == "partial"
    assert evidence_by_field["email"].outcome == "conflict"
    assert evidence_by_field["email"].score == 0.0
    assert evidence_by_field["email"].contribution == 0.0


@pytest.mark.parametrize(
    "missing",
    [None, pd.NA, pd.NaT, np.datetime64("NaT", "ns")],
)
def test_missing_values_are_explained_without_becoming_conflicts(missing):
    result = match_entities(
        [{"customer_id": missing}],
        [{"customer_id": missing}],
        fields=["customer_id"],
    )[0]

    field_evidence = result.explanation.field_evidence[0]

    assert result.status == "no_match"
    assert field_evidence.outcome == "missing"
    assert field_evidence.comparable is False
    assert field_evidence.score is None
    assert field_evidence.contribution is None
    assert result.explanation.decision.best_score == 0.0


def test_review_threshold_decision_explains_actual_threshold():
    result = match_entities(
        [{"name": "Rahul Kumar"}],
        [{"name": "Rahul K"}],
        fields=["name"],
        high_confidence_threshold=0.95,
        review_threshold=0.90,
    )[0]

    decision = result.explanation.decision

    assert result.status == "review_required"
    assert decision.decision == "review_required"
    assert decision.rule == "high_confidence_threshold"
    assert decision.threshold == 0.95
    assert decision.best_score == result.confidence
    assert decision.second_best_score is None
    assert decision.score_gap is None


def test_ambiguity_explanation_contains_actual_candidate_scores():
    result = match_entities(
        [{"name": "Rahul Kumar"}],
        [{"name": "Rahul K"}, {"name": "Rahul Kumar S"}],
        fields=["name"],
        high_confidence_threshold=0.98,
        review_threshold=0.70,
        ambiguity_margin=0.20,
    )[0]

    decision = result.explanation.decision

    assert result.status == "review_required"
    assert result.reason == "ambiguous_candidates"
    assert decision.rule == "ambiguity_margin"
    assert decision.best_score == result.confidence
    assert decision.second_best_score is not None
    assert decision.score_gap == (
        decision.best_score - decision.second_best_score
    )


def test_high_confidence_near_tie_requires_review_without_reservation():
    results = match_entities(
        [{"name": "Rahul Kumar"}],
        [{"name": "Rahul Kumar"}, {"name": "Rahul Kumar"}],
        fields=["name"],
        ambiguity_margin=0.05,
    )

    result = results[0]
    assert result.status == "review_required"
    assert result.target_index is None
    assert result.reason == "ambiguous_candidates"
    assert result.confidence == 1.0
    assert result.explanation.decision.score_gap == 0.0


def test_equal_scores_are_deterministic_and_do_not_use_input_order_as_match():
    targets = [{"name": "Rahul K"}, {"name": "Rahul Kumar S"}]

    first = match_entities(
        [{"name": "Rahul Kumar"}],
        targets,
        fields=["name"],
        high_confidence_threshold=0.98,
        review_threshold=0.70,
        ambiguity_margin=0.20,
    )[0]
    second = match_entities(
        [{"name": "Rahul Kumar"}],
        list(reversed(targets)),
        fields=["name"],
        high_confidence_threshold=0.98,
        review_threshold=0.70,
        ambiguity_margin=0.20,
    )[0]

    assert first.status == second.status == "review_required"
    assert first.target_index is None
    assert second.target_index is None
    assert first.explanation.decision.score_gap == second.explanation.decision.score_gap


def test_explanation_has_no_raw_source_or_target_values():
    source_value = "source-secret@example.com"
    target_value = "target-secret@example.com"
    result = match_entities(
        [{"email": source_value}],
        [{"email": target_value}],
        fields=["email"],
    )[0]

    serialized = repr(asdict(result.explanation))

    assert source_value not in serialized
    assert target_value not in serialized


def test_target_uniqueness_remains_unchanged_and_is_explained():
    results = match_entities(
        [{"name": "Rahul Kumar"}, {"name": "Rahul Kumar"}],
        [{"name": "Rahul Kumar"}],
        fields=["name"],
    )

    assert results[0].status == "matched"
    assert results[1].status == "no_match"
    assert results[1].reason == "no_candidate"
    assert results[1].explanation.decision.rule == "no_candidate"


def test_exact_match_across_multiple_fields_has_full_confidence():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "RAHUL KUMAR", "email": "RAHUL@EXAMPLE.COM"}],
        fields=["name", "email"],
    )[0]

    assert result.status == "matched"
    assert result.confidence == 1.0
    assert result.field_scores == {"name": 1.0, "email": 1.0}


def test_conflicting_comparable_field_reduces_confidence():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "Anitha Rao", "email": "rahul@example.com"}],
        fields=["name", "email"],
    )[0]

    assert result.status == "no_match"
    assert result.target_index is None
    assert result.confidence < 0.75


def test_zero_similarity_conflict_is_not_discarded():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "zzzzzzzzzzzz", "email": "rahul@example.com"}],
        fields=["name", "email"],
    )[0]

    assert result.status == "no_match"
    assert result.target_index is None
    assert result.confidence == 0.5


def test_multiple_conflicting_fields_do_not_match_on_one_field():
    result = match_entities(
        [{
            "name": "Rahul Kumar",
            "email": "rahul@example.com",
            "customer_id": "C001",
        }],
        [{
            "name": "Anitha Rao",
            "email": "anitha@example.com",
            "customer_id": "C001",
        }],
        fields=["name", "email", "customer_id"],
    )[0]

    assert result.status == "no_match"
    assert result.confidence < 0.75


def test_missing_source_value_is_excluded_from_comparable_score():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": None}],
        [{"name": "Rahul Kumar", "email": "other@example.com"}],
        fields=["name", "email"],
    )[0]

    assert result.status == "matched"
    assert result.confidence == 1.0
    assert result.field_scores == {"name": 1.0}


def test_missing_target_value_is_excluded_from_comparable_score():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "Rahul Kumar", "email": None}],
        fields=["name", "email"],
    )[0]

    assert result.status == "matched"
    assert result.confidence == 1.0
    assert result.field_scores == {"name": 1.0}


def test_both_missing_values_are_not_comparable():
    result = match_entities(
        [{"name": None, "email": "rahul@example.com"}],
        [{"name": None, "email": None}],
        fields=["name", "email"],
    )[0]

    assert result.status == "no_match"
    assert result.confidence == 0.0
    assert result.target_index is None


def test_records_with_no_comparable_fields_do_not_match():
    result = match_entities(
        [{"name": None, "email": "N/A"}],
        [{"name": "", "email": float("nan")}],
        fields=["name", "email"],
    )[0]

    assert result.status == "no_match"
    assert result.confidence == 0.0


def test_partial_match_is_reviewed_at_configured_threshold():
    result = match_entities(
        [{"name": "Rahul Kumar"}],
        [{"name": "Rahul K"}],
        fields=["name"],
        high_confidence_threshold=0.95,
        review_threshold=0.90,
    )[0]

    assert result.status == "review_required"
    assert result.target_index == 0
    assert result.confidence == 0.9


def test_confidence_is_finite_and_bounded():
    results = match_entities(
        [{"name": "Rahul Kumar", "email": "rahul@example.com"}],
        [{"name": "Anitha Rao", "email": "other@example.com"}],
        fields=["name", "email"],
    )

    assert math.isfinite(results[0].confidence)
    assert 0.0 <= results[0].confidence <= 1.0


def test_moderate_match_requires_review():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Rahul K"}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.95,
        review_threshold=0.70,
    )

    assert results[0].status == "review_required"
    assert results[0].target_index == 0
    assert results[0].reason == (
        "confidence_below_auto_match_threshold"
    )


def test_low_confidence_is_not_matched():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Anitha Rao"}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.90,
        review_threshold=0.80,
    )

    assert results[0].status == "no_match"
    assert results[0].target_index is None


def test_ambiguous_candidates_require_review():
    source = [
        {"name": "Rahul Kumar"}
    ]

    target = [
        {"name": "Rahul K"},
        {"name": "Rahul Kumar S"},
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
        high_confidence_threshold=0.98,
        review_threshold=0.70,
        ambiguity_margin=0.20,
    )

    assert results[0].status == "review_required"
    assert results[0].target_index is None
    assert results[0].reason == "ambiguous_candidates"


def test_target_is_used_only_once():
    source = [
        {"name": "Rahul Kumar"},
        {"name": "Rahul Kumar"},
    ]

    target = [
        {"name": "Rahul Kumar"},
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
    )

    matched = [
        result
        for result in results
        if result.status == "matched"
    ]

    assert len(matched) == 1
    assert results[1].status == "no_match"
    assert results[1].target_index is None


def test_missing_values_do_not_create_matches():
    source = [
        {"name": None}
    ]

    target = [
        {"name": None}
    ]

    results = match_entities(
        source,
        target,
        fields=["name"],
    )

    assert results[0].status == "no_match"
    assert results[0].target_index is None


def test_mixed_missing_identifier_representations_do_not_match():
    results = match_entities(
        [{"name": pd.NA}],
        [{"name": np.datetime64("NaT", "ns")}],
        fields=["name"],
    )

    assert results[0].status == "no_match"
    assert results[0].target_index is None


def test_populated_value_remains_comparable_next_to_missing_value():
    result = match_entities(
        [{"name": "Rahul Kumar", "email": pd.NA}],
        [{"name": "Rahul Kumar", "email": "other@example.com"}],
        fields=["name", "email"],
    )[0]

    assert result.status == "matched"
    assert result.confidence == 1.0
    assert result.field_scores == {"name": 1.0}


def test_invalid_thresholds_are_rejected():
    source = [{"name": "Rahul"}]
    target = [{"name": "Rahul"}]

    try:
        match_entities(
            source,
            target,
            fields=["name"],
            review_threshold=0.95,
            high_confidence_threshold=0.80,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid thresholds."
        )
