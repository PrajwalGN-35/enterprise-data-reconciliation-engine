import pandas as pd
import pytest

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

