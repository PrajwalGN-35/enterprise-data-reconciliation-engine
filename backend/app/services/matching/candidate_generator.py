from typing import Any

from app.services.matching.models import MatchCandidate
from app.services.matching.similarity import normalize_for_similarity


def generate_candidates(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    field: str,
) -> list[MatchCandidate]:
    """
    Generate candidate record pairs using a normalized field value.

    Missing values are excluded.
    """
    target_index: dict[str, list[int]] = {}

    for target_position, target_record in enumerate(target_records):
        normalized_value = normalize_for_similarity(
            target_record.get(field)
        )

        if not normalized_value:
            continue

        target_index.setdefault(
            normalized_value,
            [],
        ).append(target_position)

    candidates: list[MatchCandidate] = []

    for source_position, source_record in enumerate(source_records):
        source_value = source_record.get(field)

        normalized_value = normalize_for_similarity(
            source_value
        )

        if not normalized_value:
            continue

        for target_position in target_index.get(
            normalized_value,
            [],
        ):
            candidates.append(
                MatchCandidate(
                    source_index=source_position,
                    target_index=target_position,
                    source_value=source_value,
                    target_value=target_records[
                        target_position
                    ].get(field),
                    field=field,
                )
            )

    return candidates
