import pandas as pd
import pytest

from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    CrossSystemIntegrationError,
    run_cross_system_reconciliation,
)


def test_cross_system_mapping_preserves_identifiers_and_uses_workflow():
    source = CrossSystemDataset(
        system_name="crm",
        dataset_name="customers",
        dataframe=pd.DataFrame(
            [{"CRM Customer ID": "CRM-1", "Full Name": "Rahul Kumar"}]
        ),
        field_mapping={
            "CRM Customer ID": "customer_id",
            "Full Name": "customer_name",
        },
        record_id_field="CRM Customer ID",
    )
    target = CrossSystemDataset(
        system_name="erp",
        dataset_name="customers",
        dataframe=pd.DataFrame(
            [{"ERP ID": "ERP-1", "Customer Name": "Rahul Kumer"}]
        ),
        field_mapping={
            "ERP ID": "customer_id",
            "Customer Name": "customer_name",
        },
        record_id_field="ERP ID",
    )

    result = run_cross_system_reconciliation(
        source,
        target,
        matching_fields=["customer_name"],
        reconciliation_fields=["customer_name"],
    )

    assert result.workflow.matches[0].status == "matched"
    assert result.workflow.matches[0].target_index == 0
    assert result.source_records[0].record_id == "CRM-1"
    assert result.target_records[0].record_id == "ERP-1"
    assert result.workflow.schema_comparison["summary"]["matched_column_count"] == 2


def test_cross_system_mapping_does_not_mutate_input_dataframes():
    source_frame = pd.DataFrame([{"Source ID": "S-1", "Name": "Rahul"}])
    target_frame = pd.DataFrame([{"Target ID": "T-1", "Name": "Rahul"}])
    source_before = source_frame.copy(deep=True)
    target_before = target_frame.copy(deep=True)

    run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm", "customers", source_frame,
            {"Source ID": "customer_id", "Name": "name"},
            "Source ID",
        ),
        CrossSystemDataset(
            "erp", "customers", target_frame,
            {"Target ID": "customer_id", "Name": "name"},
            "Target ID",
        ),
        ["name"],
        ["name"],
    )

    pd.testing.assert_frame_equal(source_frame, source_before)
    pd.testing.assert_frame_equal(target_frame, target_before)


@pytest.mark.parametrize(
    "source,target,match",
    [
        (
            CrossSystemDataset("crm", "customers", pd.DataFrame([{"id": "1"}])),
            CrossSystemDataset("erp", "customers", pd.DataFrame([{"id": "1"}])),
            ["name"],
        ),
        (
            CrossSystemDataset(
                "crm", "customers", pd.DataFrame([{"id": "1"}]),
                {"missing": "name"},
            ),
            CrossSystemDataset("erp", "customers", pd.DataFrame([{"name": "Rahul"}])),
            ["name"],
        ),
    ],
)
def test_cross_system_invalid_or_incompatible_inputs_raise_clear_errors(
    source,
    target,
    match,
):
    with pytest.raises(CrossSystemIntegrationError):
        run_cross_system_reconciliation(
            source,
            target,
            matching_fields=match,
            reconciliation_fields=match,
        )


def test_cross_system_empty_inputs_return_structured_empty_result():
    result = run_cross_system_reconciliation(
        CrossSystemDataset("crm", "customers", pd.DataFrame(columns=["name"])),
        CrossSystemDataset("erp", "customers", pd.DataFrame(columns=["name"])),
        matching_fields=["name"],
        reconciliation_fields=["name"],
    )

    assert result.workflow.matches == []
    assert result.source_records == ()
    assert result.target_records == ()


def test_cross_system_preserves_ambiguity_and_target_uniqueness():
    source = CrossSystemDataset(
        "crm",
        "customers",
        pd.DataFrame(
            [
                {"source_id": "S-1", "name": "Rahul Kumar"},
                {"source_id": "S-2", "name": "Rahul Kumar"},
            ]
        ),
        record_id_field="source_id",
    )
    target = CrossSystemDataset(
        "erp",
        "customers",
        pd.DataFrame(
            [
                {"target_id": "T-1", "name": "Rahul Kumar"},
                {"target_id": "T-2", "name": "Rahul Kumar"},
            ]
        ),
        record_id_field="target_id",
    )

    result = run_cross_system_reconciliation(
        source,
        target,
        matching_fields=["name"],
        reconciliation_fields=["name"],
    )

    assert [match.status for match in result.workflow.matches] == [
        "review_required",
        "review_required",
    ]
    assert all(
        match.explanation.decision.rule == "ambiguity_margin"
        for match in result.workflow.matches
    )