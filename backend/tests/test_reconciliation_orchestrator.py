import pandas as pd
import pytest

import app.services.reconciliation.orchestrator as orchestrator
from app.services.reconciliation.orchestrator import (
    run_reconciliation_workflow,
)


def test_workflow_reconciles_matching_records():
    source = pd.DataFrame(
        [
            {
                "Customer ID": "C001",
                "Customer Name": "Alice",
                "Email": "alice@example.com",
                "Amount": "1000",
            },
            {
                "Customer ID": "C002",
                "Customer Name": "Bob",
                "Email": "bob@example.com",
                "Amount": "2000",
            },
        ]
    )

    target = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "customer_name": "Alice",
                "email": "alice@example.com",
                "amount": "1000",
            },
            {
                "customer_id": "C002",
                "customer_name": "Bob",
                "email": "bob@example.com",
                "amount": "2000",
            },
        ]
    )

    result = run_reconciliation_workflow(
        source_dataframe=source,
        target_dataframe=target,
        matching_fields=["customer_id"],
        reconciliation_fields=[
            "customer_name",
            "email",
            "amount",
        ],
    )

    assert result.summary.source_record_count == 2
    assert result.summary.target_record_count == 2
    assert result.summary.matched_record_count == 2
    assert result.summary.discrepancy_record_count == 0
    assert result.summary.reconciliation_percentage == 100.0
    assert result.schema_comparison["summary"]["matched_column_count"] == 4

    # Phase 7.4: explanations must survive the complete reconciliation workflow.
    assert len(result.matches) == 2
    for match in result.matches:
        assert match.explanation is not None
        assert match.explanation.field_evidence
        assert match.explanation.decision is not None
        assert match.explanation.decision.rule


def test_workflow_detects_field_discrepancy():
    source = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "email": "alice@example.com",
                "amount": "1000",
            }
        ]
    )

    target = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "email": "alice@different.com",
                "amount": "1000",
            }
        ]
    )

    result = run_reconciliation_workflow(
        source_dataframe=source,
        target_dataframe=target,
        matching_fields=["customer_id"],
        reconciliation_fields=["email", "amount"],
    )

    assert result.summary.matched_record_count == 0
    assert result.summary.discrepancy_record_count == 1
    assert result.summary.total_discrepancy_count == 1
    assert result.summary.field_discrepancy_counts == {
        "email": 1,
    }


def test_workflow_detects_missing_target():
    source = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "email": "alice@example.com",
            },
            {
                "customer_id": "C002",
                "email": "bob@example.com",
            },
        ]
    )

    target = pd.DataFrame(
        [
            {
                "customer_id": "C001",
                "email": "alice@example.com",
            }
        ]
    )

    result = run_reconciliation_workflow(
        source_dataframe=source,
        target_dataframe=target,
        matching_fields=["customer_id"],
        reconciliation_fields=["email"],
    )

    assert result.summary.missing_target_record_count == 1
    assert result.summary.matched_record_count == 1
    assert result.summary.reconciliation_percentage == 50.0


def test_workflow_invokes_candidate_generation_and_preserves_fuzzy_recall(
    monkeypatch,
):
    calls = []
    real_generator = orchestrator.generate_candidates

    def recording_generator(*args, **kwargs):
        candidates = real_generator(*args, **kwargs)
        calls.append((kwargs, candidates))
        return candidates

    monkeypatch.setattr(
        orchestrator,
        "generate_candidates",
        recording_generator,
    )

    result = run_reconciliation_workflow(
        source_dataframe=pd.DataFrame(
            [{"name": "Rahul Kumar", "amount": 100}]
        ),
        target_dataframe=pd.DataFrame(
            [
                {"name": "Rahul Kumer", "amount": 100},
                {"name": "Anitha Rao", "amount": 100},
            ]
        ),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert len(calls) == 1
    assert calls[0][0]["fallback_prefix_length"] == 3
    assert calls[0][0]["candidate_limit"] is None
    assert [candidate.target_index for candidate in calls[0][1]] == [0]
    assert result.matches[0].status == "matched"
    assert result.matches[0].target_index == 0


def test_workflow_falls_back_to_full_target_scan_when_no_candidates_exist():
    result = run_reconciliation_workflow(
        source_dataframe=pd.DataFrame(
            [{"name": "Rahul Kumar", "amount": 100}]
        ),
        target_dataframe=pd.DataFrame(
            [{"name": "Anitha Rao", "amount": 100}]
        ),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert result.matches[0].status == "no_match"
    assert result.matches[0].reason == "confidence_below_review_threshold"


def test_workflow_does_not_match_missing_identifiers():
    source = pd.DataFrame([{"customer_id": pd.NA, "email": "a@example.com"}])
    target = pd.DataFrame([{"customer_id": pd.NaT, "email": "a@example.com"}])

    result = run_reconciliation_workflow(
        source_dataframe=source,
        target_dataframe=target,
        matching_fields=["customer_id"],
        reconciliation_fields=["email"],
    )

    assert result.matches[0].status == "no_match"
    assert result.matches[0].target_index is None
    assert result.summary.missing_target_record_count == 1


def test_workflow_requires_matching_fields():
    source = pd.DataFrame([{"customer_id": "C001"}])
    target = pd.DataFrame([{"customer_id": "C001"}])

    with pytest.raises(
        ValueError,
        match="At least one matching field",
    ):
        run_reconciliation_workflow(
            source,
            target,
            matching_fields=[],
            reconciliation_fields=["customer_id"],
        )


def test_workflow_rejects_missing_matching_field():
    source = pd.DataFrame([{"customer_id": "C001"}])
    target = pd.DataFrame([{"customer_id": "C001"}])

    with pytest.raises(
        ValueError,
        match="Missing matching fields",
    ):
        run_reconciliation_workflow(
            source,
            target,
            matching_fields=["customer_identifier"],
            reconciliation_fields=["customer_id"],
        )


def test_workflow_requires_reconciliation_fields():
    source = pd.DataFrame([{"customer_id": "C001"}])
    target = pd.DataFrame([{"customer_id": "C001"}])

    with pytest.raises(
        ValueError,
        match="At least one reconciliation field",
    ):
        run_reconciliation_workflow(
            source,
            target,
            matching_fields=["customer_id"],
            reconciliation_fields=[],
        )


def test_workflow_rejects_missing_reconciliation_field():
    source = pd.DataFrame([{"customer_id": "C001"}])
    target = pd.DataFrame([{"customer_id": "C001"}])

    with pytest.raises(
        ValueError,
        match="Missing reconciliation fields",
    ):
        run_reconciliation_workflow(
            source,
            target,
            matching_fields=["customer_id"],
            reconciliation_fields=["email"],
        )

