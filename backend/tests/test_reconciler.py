from app.services.matching.models import EntityMatch
from app.services.reconciliation.reconciler import (
    compare_field_values,
    reconcile_matches,
)


def test_equal_values_are_reconciled():
    assert compare_field_values(
        "Prajwal@gmail.com",
        "prajwal@gmail.com",
    ) == "equal"


def test_different_values_are_discrepancies():
    assert compare_field_values(
        "prajwal@gmail.com",
        "other@gmail.com",
    ) == "discrepancy"


def test_missing_values_are_equal():
    assert compare_field_values(
        None,
        None,
    ) == "equal"


def test_matched_records_with_no_differences():
    source = [
        {
            "customer_id": "C001",
            "name": "Prajwal",
            "email": "prajwal@gmail.com",
        }
    ]

    target = [
        {
            "customer_id": "C001",
            "name": "Prajwal",
            "email": "prajwal@gmail.com",
        }
    ]

    matches = [
        EntityMatch(
            source_index=0,
            target_index=0,
            status="matched",
            confidence=1.0,
            method="fuzzy",
        )
    ]

    results = reconcile_matches(
        source,
        target,
        matches,
        fields=["customer_id", "name", "email"],
    )

    assert len(results) == 1
    assert results[0].status == "matched"
    assert results[0].discrepancies == []
    assert results[0].compared_field_count == 3
    assert results[0].discrepancy_count == 0


def test_matched_records_report_field_discrepancies():
    source = [
        {
            "customer_id": "C001",
            "name": "Prajwal",
            "email": "prajwal@gmail.com",
            "amount": "1000",
        }
    ]

    target = [
        {
            "customer_id": "C001",
            "name": "Prajwal",
            "email": "wrong@gmail.com",
            "amount": "1200",
        }
    ]

    matches = [
        EntityMatch(
            source_index=0,
            target_index=0,
            status="matched",
            confidence=1.0,
            method="fuzzy",
        )
    ]

    results = reconcile_matches(
        source,
        target,
        matches,
        fields=[
            "customer_id",
            "name",
            "email",
            "amount",
        ],
    )

    assert results[0].status == "discrepancy"
    assert results[0].discrepancy_count == 2

    discrepancy_fields = {
        item.field
        for item in results[0].discrepancies
    }

    assert discrepancy_fields == {
        "email",
        "amount",
    }


def test_no_match_becomes_missing_target():
    source = [{"customer_id": "C001"}]
    target = []

    matches = [
        EntityMatch(
            source_index=0,
            target_index=None,
            status="no_match",
            confidence=0.0,
            method="fuzzy",
            reason="no_candidate",
        )
    ]

    results = reconcile_matches(
        source,
        target,
        matches,
        fields=["customer_id"],
    )

    assert results[0].status == "missing_target"
    assert results[0].target_index is None
    assert results[0].reason == "no_candidate"


def test_review_match_remains_review_required():
    source = [{"customer_id": "C001"}]
    target = [{"customer_id": "C001"}]

    matches = [
        EntityMatch(
            source_index=0,
            target_index=None,
            status="review_required",
            confidence=0.82,
            method="fuzzy",
            reason="ambiguous_candidates",
        )
    ]

    results = reconcile_matches(
        source,
        target,
        matches,
        fields=["customer_id"],
    )

    assert results[0].status == "review_required"
    assert results[0].reason == "ambiguous_candidates"


def test_match_count_must_equal_source_count():
    source = [{"customer_id": "C001"}]
    target = [{"customer_id": "C001"}]

    try:
        reconcile_matches(
            source,
            target,
            [],
            fields=["customer_id"],
        )
    except ValueError as error:
        assert "number of entity matches" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for mismatched match count."
        )


def test_invalid_target_index_is_rejected():
    source = [{"customer_id": "C001"}]
    target = [{"customer_id": "C001"}]

    matches = [
        EntityMatch(
            source_index=0,
            target_index=5,
            status="matched",
            confidence=1.0,
            method="fuzzy",
        )
    ]

    try:
        reconcile_matches(
            source,
            target,
            matches,
            fields=["customer_id"],
        )
    except ValueError as error:
        assert "out of range" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for invalid target index."
        )
