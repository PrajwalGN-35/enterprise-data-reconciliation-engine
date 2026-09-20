from dataclasses import dataclass, field

from app.services.reconciliation.reconciler import ReconciliationResult


@dataclass
class ReconciliationSummary:
    source_record_count: int
    target_record_count: int
    matched_record_count: int
    discrepancy_record_count: int
    missing_target_record_count: int
    review_required_record_count: int
    total_discrepancy_count: int
    reconciliation_percentage: float
    exception_percentage: float
    field_discrepancy_counts: dict[str, int] = field(default_factory=dict)


def summarize_reconciliation(
    results: list[ReconciliationResult],
    source_record_count: int,
    target_record_count: int,
) -> ReconciliationSummary:
    """
    Build aggregate reconciliation metrics from record-level results.

    A record is considered fully reconciled only when its status
    is 'matched'. Discrepancies, missing targets, and review-required
    records are treated as exceptions.

    The supplied source/target counts represent the complete datasets.
    Reconciliation results must contain exactly one outcome for each
    source record.
    """

    if source_record_count < 0:
        raise ValueError("source_record_count cannot be negative.")

    if target_record_count < 0:
        raise ValueError("target_record_count cannot be negative.")

    if len(results) != source_record_count:
        raise ValueError(
            "Reconciliation results must contain exactly one result "
            "for each source record."
        )

    matched_record_count = 0
    discrepancy_record_count = 0
    missing_target_record_count = 0
    review_required_record_count = 0
    total_discrepancy_count = 0

    field_discrepancy_counts: dict[str, int] = {}

    for result in results:
        if result.status == "matched":
            matched_record_count += 1

        elif result.status == "discrepancy":
            discrepancy_record_count += 1

        elif result.status == "missing_target":
            missing_target_record_count += 1

        elif result.status == "review_required":
            review_required_record_count += 1

        else:
            raise ValueError(
                f"Unsupported reconciliation status: '{result.status}'."
            )

        total_discrepancy_count += result.discrepancy_count

        for discrepancy in result.discrepancies:
            field_discrepancy_counts[discrepancy.field] = (
                field_discrepancy_counts.get(discrepancy.field, 0) + 1
            )

    reconciliation_percentage = (
        (matched_record_count / source_record_count) * 100
        if source_record_count > 0
        else 0.0
    )

    exception_record_count = (
        discrepancy_record_count
        + missing_target_record_count
        + review_required_record_count
    )

    exception_percentage = (
        (exception_record_count / source_record_count) * 100
        if source_record_count > 0
        else 0.0
    )

    return ReconciliationSummary(
        source_record_count=source_record_count,
        target_record_count=target_record_count,
        matched_record_count=matched_record_count,
        discrepancy_record_count=discrepancy_record_count,
        missing_target_record_count=missing_target_record_count,
        review_required_record_count=review_required_record_count,
        total_discrepancy_count=total_discrepancy_count,
        reconciliation_percentage=round(reconciliation_percentage, 2),
        exception_percentage=round(exception_percentage, 2),
        field_discrepancy_counts=field_discrepancy_counts,
    )
