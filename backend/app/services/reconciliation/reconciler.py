from dataclasses import dataclass, field
from typing import Any

from app.services.matching.models import EntityMatch
from app.services.matching.similarity import normalize_for_similarity


@dataclass(frozen=True)
class FieldDiscrepancy:
    field: str
    source_value: Any
    target_value: Any
    status: str


@dataclass
class ReconciliationResult:
    source_index: int
    target_index: int | None
    status: str
    discrepancies: list[FieldDiscrepancy] = field(
        default_factory=list
    )
    compared_field_count: int = 0
    discrepancy_count: int = 0
    reason: str | None = None


def compare_field_values(
    source_value: Any,
    target_value: Any,
) -> str:
    """
    Compare two values using the project's normalized
    similarity representation.

    Returns:
        equal
        discrepancy
    """
    source_normalized = normalize_for_similarity(source_value)
    target_normalized = normalize_for_similarity(target_value)

    if source_normalized == target_normalized:
        return "equal"

    return "discrepancy"


def reconcile_matches(
    source_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    matches: list[EntityMatch],
    fields: list[str],
) -> list[ReconciliationResult]:
    """
    Reconcile matched entities field by field.

    Entity matching determines which records correspond.
    Reconciliation determines whether their compared values
    agree or contain discrepancies.
    """

    if not fields:
        raise ValueError(
            "At least one reconciliation field is required."
        )

    if len(matches) != len(source_records):
        raise ValueError(
            "The number of entity matches must equal "
            "the number of source records."
        )

    results: list[ReconciliationResult] = []

    for source_index, match in enumerate(matches):
        if match.status == "no_match":
            results.append(
                ReconciliationResult(
                    source_index=source_index,
                    target_index=None,
                    status="missing_target",
                    reason=match.reason,
                )
            )
            continue

        if match.status == "review_required":
            results.append(
                ReconciliationResult(
                    source_index=source_index,
                    target_index=match.target_index,
                    status="review_required",
                    reason=match.reason,
                )
            )
            continue

        if match.target_index is None:
            results.append(
                ReconciliationResult(
                    source_index=source_index,
                    target_index=None,
                    status="missing_target",
                    reason="matched_without_target_index",
                )
            )
            continue

        if match.target_index >= len(target_records):
            raise ValueError(
                f"Target index {match.target_index} is out of range."
            )

        source_record = source_records[source_index]
        target_record = target_records[match.target_index]

        discrepancies: list[FieldDiscrepancy] = []

        for field in fields:
            source_value = source_record.get(field)
            target_value = target_record.get(field)

            comparison_status = compare_field_values(
                source_value,
                target_value,
            )

            if comparison_status == "discrepancy":
                discrepancies.append(
                    FieldDiscrepancy(
                        field=field,
                        source_value=source_value,
                        target_value=target_value,
                        status="discrepancy",
                    )
                )

        if discrepancies:
            status = "discrepancy"
        else:
            status = "matched"

        results.append(
            ReconciliationResult(
                source_index=source_index,
                target_index=match.target_index,
                status=status,
                discrepancies=discrepancies,
                compared_field_count=len(fields),
                discrepancy_count=len(discrepancies),
            )
        )

    return results
