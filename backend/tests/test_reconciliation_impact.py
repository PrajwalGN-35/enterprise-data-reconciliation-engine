import pytest

from app.services.reconciliation.impact import (
    DiscrepancyImpactConfig,
    analyze_reconciliation_impact,
)
from app.services.reconciliation.reconciler import (
    FieldDiscrepancy,
    ReconciliationResult,
)


def test_weighted_discrepancy_is_prioritized_and_sorted():
    results = [
        ReconciliationResult(
            source_index=0,
            target_index=0,
            status="discrepancy",
            discrepancies=[
                FieldDiscrepancy("email", "secret-source", "secret-target", "discrepancy")
            ],
            compared_fields=("email", "amount"),
        ),
        ReconciliationResult(
            source_index=1,
            target_index=None,
            status="missing_target",
        ),
        ReconciliationResult(
            source_index=2,
            target_index=2,
            status="matched",
        ),
    ]

    analysis = analyze_reconciliation_impact(
        results,
        source_record_count=3,
        config=DiscrepancyImpactConfig(
            field_weights={"email": 1.0, "amount": 4.0},
            missing_target_weight=0.9,
        ),
    )

    assert analysis.affected_record_count == 2
    assert analysis.exceptions[0].source_index == 1
    assert analysis.exceptions[0].impact_score == 0.9
    assert analysis.exceptions[0].priority == "critical"
    assert analysis.exceptions[1].impact_score == 0.5
    assert analysis.exceptions[1].priority == "medium"
    assert analysis.exceptions[1].discrepant_fields == ("email",)
    assert analysis.total_impact_score == 1.4


def test_review_and_discrepancy_use_status_baselines():
    results = [
        ReconciliationResult(0, None, "review_required"),
        ReconciliationResult(
            1,
            1,
            "discrepancy",
            compared_fields=("name",),
        ),
    ]

    analysis = analyze_reconciliation_impact(results, 2)

    assert [item.impact_score for item in analysis.exceptions] == [0.75, 0.5]
    assert analysis.exceptions[0].reason_codes == (
        "status_review_required",
        "priority_high",
    )


def test_empty_results_are_supported():
    analysis = analyze_reconciliation_impact([], 0)

    assert analysis.affected_record_count == 0
    assert analysis.total_impact_score == 0.0
    assert analysis.exceptions == ()


@pytest.mark.parametrize(
    "config_factory",
    [
        lambda: DiscrepancyImpactConfig(
            critical_threshold=0.5,
            high_threshold=0.5,
            medium_threshold=0.2,
        ),
        lambda: DiscrepancyImpactConfig(default_field_weight=0),
    ],
)
def test_invalid_impact_configuration_is_rejected(config_factory):
    with pytest.raises(ValueError):
        config_factory()


def test_invalid_results_are_rejected():
    with pytest.raises(ValueError, match="exactly one result"):
        analyze_reconciliation_impact([], 1)

    with pytest.raises(ValueError, match="Unsupported reconciliation status"):
        analyze_reconciliation_impact(
            [ReconciliationResult(0, None, "unknown")],
            1,
        )


def test_analysis_does_not_include_raw_values():
    result = ReconciliationResult(
        0,
        0,
        "discrepancy",
        discrepancies=[
            FieldDiscrepancy(
                "email",
                "source-secret@example.com",
                "target-secret@example.com",
                "discrepancy",
            )
        ],
        compared_fields=("email",),
    )

    serialized = repr(analyze_reconciliation_impact([result], 1))

    assert "source-secret@example.com" not in serialized
    assert "target-secret@example.com" not in serialized

@pytest.mark.parametrize("invalid_count", [True, 1.5, "1", -1])
def test_impact_analysis_rejects_invalid_source_record_counts(invalid_count):
    with pytest.raises(ValueError, match="non-negative integer"):
        analyze_reconciliation_impact([], invalid_count)


def test_impact_analysis_rejects_duplicate_source_indices():
    results = [
        ReconciliationResult(0, 0, "matched"),
        ReconciliationResult(0, 1, "matched"),
    ]

    with pytest.raises(ValueError, match="unique source_index"):
        analyze_reconciliation_impact(results, 2)


@pytest.mark.parametrize("invalid_index", [-1, 1, True, 0.5])
def test_impact_analysis_rejects_invalid_source_indices(invalid_index):
    results = [ReconciliationResult(invalid_index, None, "matched")]

    with pytest.raises(ValueError, match="source_index"):
        analyze_reconciliation_impact(results, 1)


def test_repeated_discrepant_fields_do_not_inflate_impact():
    result = ReconciliationResult(
        source_index=0,
        target_index=0,
        status="discrepancy",
        discrepancies=[
            FieldDiscrepancy("email", "a", "b", "discrepancy"),
            FieldDiscrepancy("email", "c", "d", "discrepancy"),
        ],
        compared_fields=("email", "amount"),
    )

    analysis = analyze_reconciliation_impact(
        [result],
        1,
        config=DiscrepancyImpactConfig(discrepancy_weight=0.1),
    )

    assert analysis.exceptions[0].discrepant_fields == ("email",)
    assert analysis.exceptions[0].impact_score == 0.5


def test_discrepant_field_must_be_compared():
    result = ReconciliationResult(
        source_index=0,
        target_index=0,
        status="discrepancy",
        discrepancies=[
            FieldDiscrepancy("email", "a", "b", "discrepancy"),
        ],
        compared_fields=("amount",),
    )

    with pytest.raises(ValueError, match="included in compared_fields"):
        analyze_reconciliation_impact([result], 1)
