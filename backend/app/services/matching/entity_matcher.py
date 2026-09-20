from typing import Any

from app.services.matching.models import EntityMatch
from app.services.matching.similarity import calculate_similarity


DEFAULT_HIGH_CONFIDENCE_THRESHOLD = 0.90
DEFAULT_REVIEW_THRESHOLD = 0.75
DEFAULT_AMBIGUITY_MARGIN = 0.05


def _score_record(
    source_record: dict[str, Any],
    target_record: dict[str, Any],
    fields: list[str],
) -> dict[str, float]:
    return {
        field: calculate_similarity(
            source_record.get(field),
            target_record.get(field),
        )
        for field in fields
    }


def _combined_score(
    field_scores: dict[str, float],
) -> float:
    valid_scores = [
        score
        for score in field_scores.values()
        if score > 0
    ]

    if not valid_scores:
        return 0.0

    return round(
        sum(valid_scores) / len(valid_scores),
        4,
    )


def match_entities(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    fields: list[str],
    high_confidence_threshold: float = DEFAULT_HIGH_CONFIDENCE_THRESHOLD,
    review_threshold: float = DEFAULT_REVIEW_THRESHOLD,
    ambiguity_margin: float = DEFAULT_AMBIGUITY_MARGIN,
) -> list[EntityMatch]:
    """
    Match source records against target records.

    The best available target is selected for each source record,
    subject to confidence and ambiguity rules.

    Each target record can be assigned to at most one source record.
    """

    if not fields:
        raise ValueError("At least one matching field is required.")

    if not 0 <= review_threshold <= high_confidence_threshold <= 1:
        raise ValueError(
            "Thresholds must satisfy "
            "0 <= review_threshold <= high_confidence_threshold <= 1."
        )

    if not 0 <= ambiguity_margin <= 1:
        raise ValueError(
            "Ambiguity margin must be between 0 and 1."
        )

    results: list[EntityMatch] = []
    used_target_indices: set[int] = set()

    for source_index, source_record in enumerate(source_records):
        ranked_candidates: list[
            tuple[float, int, dict[str, float]]
        ] = []

        for target_index, target_record in enumerate(target_records):
            if target_index in used_target_indices:
                continue

            field_scores = _score_record(
                source_record,
                target_record,
                fields,
            )

            score = _combined_score(field_scores)

            if score <= 0:
                continue

            ranked_candidates.append(
                (
                    score,
                    target_index,
                    field_scores,
                )
            )

        ranked_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        if not ranked_candidates:
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="no_match",
                    confidence=0.0,
                    method="fuzzy",
                    reason="no_candidate",
                )
            )
            continue

        best_score, best_target, best_field_scores = (
            ranked_candidates[0]
        )

        if len(ranked_candidates) > 1:
            second_score = ranked_candidates[1][0]

            if (
                best_score < high_confidence_threshold
                and best_score - second_score
                < ambiguity_margin
            ):
                results.append(
                    EntityMatch(
                        source_index=source_index,
                        target_index=None,
                        status="review_required",
                        confidence=best_score,
                        method="fuzzy",
                        field_scores=best_field_scores,
                        reason="ambiguous_candidates",
                    )
                )
                continue

        if best_score >= high_confidence_threshold:
            status = "matched"
            reason = None
        elif best_score >= review_threshold:
            status = "review_required"
            reason = "confidence_below_auto_match_threshold"
        else:
            status = "no_match"
            reason = "confidence_below_review_threshold"

        if status != "no_match":
            used_target_indices.add(best_target)

        results.append(
            EntityMatch(
                source_index=source_index,
                target_index=(
                    best_target
                    if status != "no_match"
                    else None
                ),
                status=status,
                confidence=best_score,
                method="fuzzy",
                field_scores=best_field_scores,
                reason=reason,
            )
        )

    return results
