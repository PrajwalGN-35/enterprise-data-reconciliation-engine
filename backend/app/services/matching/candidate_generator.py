from typing import Any, Iterable

from app.services.matching.models import MatchCandidate
from app.services.matching.similarity import normalize_for_similarity


def generate_candidates(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    field: str,
    *,
    blocking_fields: Iterable[str] | None = None,
    fallback_prefix_length: int | None = None,
    candidate_limit: int | None = None,
) -> list[MatchCandidate]:
    """
    Generate candidate record pairs using deterministic blocking strategies.

    The original normalized exact block remains the default. Additional
    blocking fields merge into the same result, and a bounded normalized
    prefix fallback can recover typo-tolerant candidates for sources that
    have no exact block hit. Missing values are never indexed.
    """
    if not isinstance(field, str) or not field.strip():
        raise ValueError("field must be a non-empty string.")

    if fallback_prefix_length is not None and (
        isinstance(fallback_prefix_length, bool)
        or not isinstance(fallback_prefix_length, int)
        or fallback_prefix_length < 1
    ):
        raise ValueError(
            "fallback_prefix_length must be a positive integer or None."
        )

    if candidate_limit is not None and (
        isinstance(candidate_limit, bool)
        or not isinstance(candidate_limit, int)
        or candidate_limit < 1
    ):
        raise ValueError("candidate_limit must be a positive integer or None.")

    fields = [field]
    for blocking_field in blocking_fields or ():
        if not isinstance(blocking_field, str) or not blocking_field.strip():
            raise ValueError("blocking_fields must contain non-empty strings.")
        if blocking_field not in fields:
            fields.append(blocking_field)

    exact_indexes: dict[str, dict[str, list[int]]] = {
        blocking_field: {}
        for blocking_field in fields
    }
    prefix_indexes: dict[str, dict[str, list[int]]] = {
        blocking_field: {}
        for blocking_field in fields
    }

    for target_position, target_record in enumerate(target_records):
        for blocking_field in fields:
            normalized_value = normalize_for_similarity(
                target_record.get(blocking_field)
            )

            if not normalized_value:
                continue

            exact_indexes[blocking_field].setdefault(
                normalized_value,
                [],
            ).append(target_position)
            if fallback_prefix_length is not None:
                prefix = normalized_value[:fallback_prefix_length]
                prefix_indexes[blocking_field].setdefault(
                    prefix,
                    [],
                ).append(target_position)

    candidates: list[MatchCandidate] = []

    for source_position, source_record in enumerate(source_records):
        source_candidates: dict[int, str] = {}
        exact_target_positions: set[int] = set()

        for blocking_field in fields:
            source_value = source_record.get(blocking_field)
            normalized_value = normalize_for_similarity(source_value)
            if not normalized_value:
                continue

            for target_position in exact_indexes[blocking_field].get(
                normalized_value,
                [],
            ):
                exact_target_positions.add(target_position)
                source_candidates.setdefault(target_position, blocking_field)

        if not exact_target_positions and fallback_prefix_length is not None:
            for blocking_field in fields:
                source_value = source_record.get(blocking_field)
                normalized_value = normalize_for_similarity(source_value)
                if not normalized_value:
                    continue

                prefix = normalized_value[:fallback_prefix_length]
                for target_position in prefix_indexes[blocking_field].get(
                    prefix,
                    [],
                ):
                    source_candidates.setdefault(target_position, blocking_field)

        ordered_candidates = sorted(
            source_candidates.items(),
            key=lambda item: (item[0], fields.index(item[1])),
        )
        if candidate_limit is not None:
            ordered_candidates = ordered_candidates[:candidate_limit]

        for target_position, blocking_field in ordered_candidates:
            candidates.append(
                MatchCandidate(
                    source_index=source_position,
                    target_index=target_position,
                    source_value=source_record.get(blocking_field),
                    target_value=target_records[target_position].get(
                        blocking_field
                    ),
                    field=blocking_field,
                )
            )

    return candidates
