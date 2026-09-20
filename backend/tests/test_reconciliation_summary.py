from app.services.reconciliation.reconciler import (
    FieldDiscrepancy,
    ReconciliationResult,
)
from app.services.reconciliation.summary import (
    summarize_reconciliation,
)


def test_summary_counts_reconciliation_statuses():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="matched",
        ),
        ReconciliationResult(
            source_index=1,
            target_index=1,
            status="discrepancy",
            discrepancies=[
                FieldDiscrepancy(
                    field="email",
                    source_value="a@example.com",
                    target_value="b@example.com",
                    status="discrepancy",
                ),
                FieldDiscrepancy(
                    field="amount",
                    source_value="1000",
                    target_value="1200",
                    status="discrepancy",
                ),
            ],
            compared_field_count=2,
            discrepancy_count=2,
        ),
        ReconciliationResult(
            source_index=2,
            target_index=None,
            status="missing_target",
        ),
        ReconciliationResult(
            source_index=3,
            target_index=None,
            status="review_required",
        ),
    ]

    summary = summarize_reconciliation(
        results,
        source_record_count=4,
        target_record_count=3,
    )

    assert summary.source_record_count == 4
    assert summary.target_record_count == 3
    assert summary.matched_record_count == 1
    assert summary.discrepancy_record_count == 1
    assert summary.missing_target_record_count == 1
    assert summary.review_required_record_count == 1
    assert summary.total_discrepancy_count == 2


def test_summary_calculates_percentages():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="matched",
        ),
        ReconciliationResult(
            source_index=1,
            target_index=1,
            status="matched",
        ),
        ReconciliationResult(
            source_index=2,
            target_index=2,
            status="discrepancy",
            discrepancy_count=1,
        ),
        ReconciliationResult(
            source_index=3,
            target_index=None,
            status="missing_target",
        ),
    ]

    summary = summarize_reconciliation(
        results,
        source_record_count=4,
        target_record_count=3,
    )

    assert summary.reconciliation_percentage == 50.0
    assert summary.exception_percentage == 50.0


def test_summary_aggregates_field_discrepancies():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="discrepancy",
            discrepancies=[
                FieldDiscrepancy(
                    field="email",
                    source_value="a",
                    target_value="b",
                    status="discrepancy",
                ),
                FieldDiscrepancy(
                    field="amount",
                    source_value="1000",
                    target_value="1200",
                    status="discrepancy",
                ),
            ],
            discrepancy_count=2,
        ),
        ReconciliationResult(
            source_index=1,
            target_index=1,
            status="discrepancy",
            discrepancies=[
                FieldDiscrepancy(
                    field="email",
                    source_value="c",
                    target_value="d",
                    status="discrepancy",
                ),
            ],
            discrepancy_count=1,
        ),
    ]

    summary = summarize_reconciliation(
        results,
        source_record_count=2,
        target_record_count=2,
    )

    assert summary.total_discrepancy_count == 3
    assert summary.field_discrepancy_counts == {
        "email": 2,
        "amount": 1,
    }


def test_empty_source_dataset_has_zero_percentages():
    summary = summarize_reconciliation(
        results=[],
        source_record_count=0,
        target_record_count=0,
    )

    assert summary.reconciliation_percentage == 0.0
    assert summary.exception_percentage == 0.0
    assert summary.matched_record_count == 0


def test_results_cannot_exceed_source_count():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="matched",
        ),
        ReconciliationResult(
            source_index=1,
            target_index=1,
            status="matched",
        ),
    ]

    try:
        summarize_reconciliation(
            results,
            source_record_count=1,
            target_record_count=2,
        )
    except ValueError as error:
        assert "exactly one result" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for excessive result count."
        )


def test_incomplete_results_are_rejected():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="matched",
        ),
    ]

    try:
        summarize_reconciliation(
            results,
            source_record_count=2,
            target_record_count=2,
        )
    except ValueError as error:
        assert "exactly one result" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for incomplete reconciliation results."
        )


def test_negative_record_counts_are_rejected():
    try:
        summarize_reconciliation(
            results=[],
            source_record_count=-1,
            target_record_count=0,
        )
    except ValueError as error:
        assert "cannot be negative" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for negative source count."
        )


def test_unknown_reconciliation_status_is_rejected():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="unknown",
        )
    ]

    try:
        summarize_reconciliation(
            results,
            source_record_count=1,
            target_record_count=1,
        )
    except ValueError as error:
        assert "Unsupported reconciliation status" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for unsupported status."
        )
