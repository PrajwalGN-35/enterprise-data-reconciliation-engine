"""Deterministic exact matching using normalized composite keys."""

from collections import Counter, defaultdict
from typing import Any

from app.services.matching.models import EntityMatch
from app.services.matching.similarity import normalize_for_similarity


def _composite_key(
    record: dict[str, Any],
    fields: list[str],
) -> tuple[str, ...] | None:
    """Build a normalized composite key, rejecting incomplete keys."""
    values: list[str] = []

    for field in fields:
        normalized = normalize_for_similarity(record.get(field))

        if not normalized:
            return None

        values.append(normalized)

    return tuple(values)


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

    source_keys = [
        _composite_key(record, fields)
        for record in source_records
    ]
    target_keys = [
        _composite_key(record, fields)
        for record in target_records
    ]

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
            )
        )

    return results