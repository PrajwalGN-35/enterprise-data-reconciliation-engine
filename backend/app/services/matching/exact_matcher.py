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

    for field in fields:
        normalized = normalize_for_similarity(record.get(field))

        if not normalized:
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="missing",
                    comparable=False,
                    explanation_code="missing_value",
                )
            )
            return _CompositeKeyResult(None, tuple(evidence))

        values.append(normalized)
        evidence.append(
            MatchFieldEvidence(
                field=field,
                outcome="exact",
                score=1.0,
                explanation_code="normalized_exact_match",
            )
        )

    return _CompositeKeyResult(tuple(values), tuple(evidence))


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
                        field_evidence=(),
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
                        field_evidence=(),
                        summary=(
                            "No target record has the same normalized "
                            "composite key."
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
                        field_evidence=(),
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
                        field_evidence=(),
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