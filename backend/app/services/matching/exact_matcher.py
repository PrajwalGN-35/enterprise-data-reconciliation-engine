"""Deterministic exact matching using normalized composite keys."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from app.services.matching.models import (
    EntityMatch,
    MatchDecisionEvidence,
    MatchExplanation,
    MatchFieldEvidence,
)
from app.services.matching.similarity import normalize_for_similarity


@dataclass(frozen=True)
class _CompositeKeyResult:
    key: tuple[str, ...] | None
    field_evidence: tuple[MatchFieldEvidence, ...]


def _composite_key_result(
    record: dict[str, Any],
    fields: list[str],
) -> _CompositeKeyResult:
    values: list[str] = []
    evidence: list[MatchFieldEvidence] = []
    has_missing_value = False

    for field in fields:
        normalized = normalize_for_similarity(record.get(field))

        if not normalized:
            has_missing_value = True
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="missing",
                    comparable=False,
                    explanation_code="missing_value",
                )
            )
            continue

        values.append(normalized)
        evidence.append(
            MatchFieldEvidence(
                field=field,
                outcome="exact",
                score=1.0,
                explanation_code="normalized_exact_match",
            )
        )

    key = None if has_missing_value else tuple(values)
    return _CompositeKeyResult(key, tuple(evidence))


def _comparison_evidence(
    source_record: dict[str, Any],
    target_record: dict[str, Any],
    fields: list[str],
) -> tuple[MatchFieldEvidence, ...]:
    """Explain normalized, field-by-field differences between two records."""
    evidence: list[MatchFieldEvidence] = []

    for field in fields:
        source_value = normalize_for_similarity(source_record.get(field))
        target_value = normalize_for_similarity(target_record.get(field))

        if not source_value or not target_value:
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="missing",
                    comparable=False,
                    explanation_code="missing_value",
                )
            )
        elif source_value == target_value:
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="exact",
                    score=1.0,
                    explanation_code="normalized_exact_match",
                )
            )
        else:
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="conflict",
                    score=0.0,
                    explanation_code="normalized_value_conflict",
                )
            )

    return tuple(evidence)


def _best_candidate_evidence(
    source_record: dict[str, Any],
    target_records: list[dict[str, Any]],
    fields: list[str],
    fallback: tuple[MatchFieldEvidence, ...],
) -> tuple[MatchFieldEvidence, ...]:
    """Explain the closest target candidate without changing match decisions."""
    if not target_records:
        return fallback

    candidates = []

    for target_index, target_record in enumerate(target_records):
        evidence = _comparison_evidence(
            source_record,
            target_record,
            fields,
        )
        exact_count = sum(item.outcome == "exact" for item in evidence)
        comparable_count = sum(item.comparable for item in evidence)

        # Prefer the most exact fields, then the most comparable fields.
        # Original target order resolves ties deterministically.
        candidates.append(
            (-exact_count, -comparable_count, target_index, evidence)
        )

    return min(candidates, key=lambda item: item[:3])[3]


def _explanation(
    *,
    decision: str,
    rule: str | None,
    field_evidence: tuple[MatchFieldEvidence, ...],
    summary: str,
) -> MatchExplanation:
    return MatchExplanation(
        field_evidence=field_evidence,
        decision=MatchDecisionEvidence(
            decision=decision,
            rule=rule,
            comparable_field_count=sum(
                item.comparable for item in field_evidence
            ),
            summary=summary,
        ),
    )


def match_entities_exact(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    fields: list[str],
) -> list[EntityMatch]:
    """
    Match records by exact normalized equality across every configured field.

    A complete composite key must exist on both sides. Duplicate keys are
    flagged for review instead of selecting an arbitrary record. A target
    is assigned at most once.

    This function performs exact matching only; it does not use fuzzy scores.
    """
    if not fields:
        raise ValueError("At least one matching field is required.")

    if any(not isinstance(field, str) or not field.strip() for field in fields):
        raise ValueError("Matching fields must be non-empty strings.")

    if len(set(fields)) != len(fields):
        raise ValueError("Matching fields must not contain duplicates.")

    source_key_results = [
        _composite_key_result(record, fields)
        for record in source_records
    ]
    target_key_results = [
        _composite_key_result(record, fields)
        for record in target_records
    ]
    source_keys = [result.key for result in source_key_results]
    target_keys = [result.key for result in target_key_results]

    source_counts = Counter(
        key for key in source_keys if key is not None
    )

    target_positions: dict[tuple[str, ...], list[int]] = defaultdict(list)

    for target_index, key in enumerate(target_keys):
        if key is not None:
            target_positions[key].append(target_index)

    used_target_indices: set[int] = set()
    results: list[EntityMatch] = []

    for source_index, key in enumerate(source_keys):
        if key is None:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="no_match",
                    confidence=0.0,
                    method="exact",
                    reason="missing_matching_value",
                    explanation=_explanation(
                        decision="no_match",
                        rule="missing_matching_value",
                        field_evidence=source_key_results[
                            source_index
                        ].field_evidence,
                        summary=(
                            "A required composite-key field is missing."
                        ),
                    ),
                )
            )
            continue

        field_scores = {field: 1.0 for field in fields}

        if source_counts[key] > 1:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="review_required",
                    confidence=1.0,
                    method="exact",
                    field_scores=field_scores,
                    reason="duplicate_source_key",
                    explanation=_explanation(
                        decision="review_required",
                        rule="duplicate_source_key",
                        field_evidence=source_key_results[
                            source_index
                        ].field_evidence,
                        summary=(
                            "The source composite key occurs more than once."
                        ),
                    ),
                )
            )
            continue

        candidates = target_positions.get(key, [])

        if not candidates:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="no_match",
                    confidence=0.0,
                    method="exact",
                    field_scores=field_scores,
                    reason="no_exact_match",
                    explanation=_explanation(
                        decision="no_match",
                        rule="no_exact_match",
                        field_evidence=_best_candidate_evidence(
                            source_records[source_index],
                            target_records,
                            fields,
                            source_key_results[source_index].field_evidence,
                        ),
                        summary=(

                            "No target records are available for comparison."

                            if not target_records

                            else (

                                "No target record has the same normalized "

                                "composite key; evidence describes the closest "

                                "target candidate."

                            )

                        ),
                    ),
                )
            )
            continue

        if len(candidates) > 1:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="review_required",
                    confidence=1.0,
                    method="exact",
                    field_scores=field_scores,
                    reason="duplicate_target_key",
                    explanation=_explanation(
                        decision="review_required",
                        rule="duplicate_target_key",
                        field_evidence=source_key_results[
                            source_index
                        ].field_evidence,
                        summary=(
                            "The target composite key occurs more than once."
                        ),
                    ),
                )
            )
            continue

        target_index = candidates[0]

        if target_index in used_target_indices:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="review_required",
                    confidence=1.0,
                    method="exact",
                    field_scores=field_scores,
                    reason="target_already_assigned",
                    explanation=_explanation(
                        decision="review_required",
                        rule="target_already_assigned",
                        field_evidence=source_key_results[
                            source_index
                        ].field_evidence,
                        summary="The matching target was already assigned.",
                    ),
                )
            )
            continue

        used_target_indices.add(target_index)

        results.append(
            EntityMatch(
                source_index=source_index,
                target_index=target_index,
                status="matched",
                confidence=1.0,
                method="exact",
                field_scores=field_scores,
                explanation=_explanation(
                    decision="matched",
                    rule="exact_composite_key_match",
                    field_evidence=target_key_results[
                        target_index
                    ].field_evidence,
                    summary="All composite-key fields matched exactly.",
                ),
            )
        )

    return results
