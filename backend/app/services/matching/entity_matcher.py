import math
from dataclasses import dataclass
from typing import Any

from app.services.matching.models import (
    EntityMatch,
    MatchDecisionEvidence,
    MatchExplanation,
    MatchFieldEvidence,
)
from app.services.matching.similarity import (
    calculate_similarity,
    normalize_for_similarity,
)


DEFAULT_HIGH_CONFIDENCE_THRESHOLD = 0.90
DEFAULT_REVIEW_THRESHOLD = 0.75
DEFAULT_AMBIGUITY_MARGIN = 0.05


@dataclass(frozen=True)
class _ScoredCandidate:
    score: float
    field_scores: dict[str, float]
    field_evidence: tuple[MatchFieldEvidence, ...]


def _score_record(
    source_record: dict[str, Any],
    target_record: dict[str, Any],
    fields: list[str],
) -> _ScoredCandidate:
    scores: dict[str, float] = {}
    evidence: list[MatchFieldEvidence] = []

    for field in fields:
        source_value = source_record.get(field)
        target_value = target_record.get(field)

        source_text = normalize_for_similarity(source_value)
        target_text = normalize_for_similarity(target_value)

        if not source_text or not target_text:
            evidence.append(
                MatchFieldEvidence(
                    field=field,
                    outcome="missing",
                    comparable=False,
                    explanation_code="missing_value",
                )
            )
            continue

        score = calculate_similarity(
            source_value,
            target_value,
        )
        scores[field] = score

        if score == 1.0:
            outcome = "exact"
            explanation_code = "normalized_exact_match"
        elif score > 0.0:
            outcome = "partial"
            explanation_code = "fuzzy_partial_match"
        else:
            outcome = "conflict"
            explanation_code = "populated_conflict"

        evidence.append(
            MatchFieldEvidence(
                field=field,
                outcome=outcome,
                score=score,
                contribution=None,
                explanation_code=explanation_code,
            )
        )

    score = _combined_score(scores)
    comparable_count = len(scores)
    if comparable_count:
        evidence = [
            MatchFieldEvidence(
                field=item.field,
                outcome=item.outcome,
                score=item.score,
                comparable=item.comparable,
                contribution=(
                    item.score / comparable_count
                    if item.score is not None
                    else None
                ),
                explanation_code=item.explanation_code,
            )
            for item in evidence
        ]

    return _ScoredCandidate(
        score=score,
        field_scores=scores,
        field_evidence=tuple(evidence),
    )


def _combined_score(
    field_scores: dict[str, float],
) -> float:
    if not field_scores:
        return 0.0

    score = sum(field_scores.values()) / len(field_scores)

    if not isinstance(score, (int, float)) or not math.isfinite(score):
        return 0.0

    return round(min(max(score, 0.0), 1.0), 4)


def _decision_explanation(
    *,
    decision: str,
    rule: str,
    threshold: float | None,
    best_score: float | None,
    second_best_score: float | None,
    comparable_field_count: int,
    field_evidence: tuple[MatchFieldEvidence, ...],
    summary: str,
) -> MatchExplanation:
    score_gap = None
    if best_score is not None and second_best_score is not None:
        score_gap = best_score - second_best_score

    return MatchExplanation(
        field_evidence=field_evidence,
        decision=MatchDecisionEvidence(
            decision=decision,
            rule=rule,
            threshold=threshold,
            best_score=best_score,
            second_best_score=second_best_score,
            score_gap=score_gap,
            comparable_field_count=comparable_field_count,
            summary=summary,
        ),
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
        ranked_candidates: list[tuple[float, int, _ScoredCandidate]] = []
        evaluated_candidates: list[tuple[float, int, _ScoredCandidate]] = []

        for target_index, target_record in enumerate(target_records):
            if target_index in used_target_indices:
                continue

            scored_candidate = _score_record(
                source_record,
                target_record,
                fields,
            )
            evaluated_candidates.append(
                (scored_candidate.score, target_index, scored_candidate)
            )

            score = scored_candidate.score

            if score <= 0:
                continue

            ranked_candidates.append(
                (
                    score,
                    target_index,
                    scored_candidate,
                )
            )

        ranked_candidates.sort(
            key=lambda item: (-item[0], item[1]),
        )

        if not ranked_candidates:
            diagnostic_candidate = max(
                evaluated_candidates,
                key=lambda item: item[0],
                default=None,
            )
            diagnostic_score = (
                diagnostic_candidate[0]
                if diagnostic_candidate is not None
                else None
            )
            diagnostic_evidence = (
                diagnostic_candidate[2].field_evidence
                if diagnostic_candidate is not None
                else ()
            )
            diagnostic_count = (
                len(diagnostic_candidate[2].field_scores)
                if diagnostic_candidate is not None
                else 0
            )
            results.append(
                EntityMatch(
                    source_index=source_index,
                    target_index=None,
                    status="no_match",
                    confidence=0.0,
                    method="fuzzy",
                    reason="no_candidate",
                    explanation=_decision_explanation(
                        decision="no_match",
                        rule="no_candidate",
                        threshold=None,
                        best_score=diagnostic_score,
                        second_best_score=None,
                        comparable_field_count=diagnostic_count,
                        field_evidence=diagnostic_evidence,
                        summary="No eligible fuzzy candidate was found.",
                    ),
                )
            )
            continue

        best_score, best_target, best_candidate = (
            ranked_candidates[0]
        )
        best_field_scores = best_candidate.field_scores
        best_field_evidence = best_candidate.field_evidence
        second_score = (
            ranked_candidates[1][0]
            if len(ranked_candidates) > 1
            else None
        )

        if len(ranked_candidates) > 1:
            if (
                best_score - second_score < ambiguity_margin
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
                        explanation=_decision_explanation(
                            decision="review_required",
                            rule="ambiguity_margin",
                            threshold=ambiguity_margin,
                            best_score=best_score,
                            second_best_score=second_score,
                            comparable_field_count=len(best_field_scores),
                            field_evidence=best_field_evidence,
                            summary=(
                                "The best candidates are within the "
                                "configured ambiguity margin."
                            ),
                        ),
                    )
                )
                continue

        if best_score >= high_confidence_threshold:
            status = "matched"
            reason = None
            decision_rule = "high_confidence_threshold"
            decision_threshold = high_confidence_threshold
            decision_summary = "The candidate met the high-confidence threshold."
        elif best_score >= review_threshold:
            status = "review_required"
            reason = "confidence_below_auto_match_threshold"
            decision_rule = "high_confidence_threshold"
            decision_threshold = high_confidence_threshold
            decision_summary = (
                "The candidate met the review threshold but not the "
                "high-confidence threshold."
            )
        else:
            status = "no_match"
            reason = "confidence_below_review_threshold"
            decision_rule = "review_threshold"
            decision_threshold = review_threshold
            decision_summary = "The candidate did not meet the review threshold."

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
                explanation=_decision_explanation(
                    decision=status,
                    rule=decision_rule,
                    threshold=decision_threshold,
                    best_score=best_score,
                    second_best_score=second_score,
                    comparable_field_count=len(best_field_scores),
                    field_evidence=best_field_evidence,
                    summary=decision_summary,
                ),
            )
        )

    return results
