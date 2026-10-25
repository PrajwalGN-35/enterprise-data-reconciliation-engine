import pandas as pd
import pytest

import app.services.reconciliation.cross_system as cross_system
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
    assert result.source_records[0].role == "source"
    assert result.target_records[0].role == "target"
    assert result.workflow.schema_comparison["summary"]["matched_column_count"] == 2


def test_match_indexes_align_with_source_and_target_references():
    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm",
            "customers",
            pd.DataFrame(
                [
                    {"id": "S-1", "name": "Rahul Kumar"},
                    {"id": "S-2", "name": "Anitha Rao"},
                    {"id": "S-3", "name": "Missing"},
                ]
            ),
            record_id_field="id",
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            pd.DataFrame(
                [
                    {"id": "T-1", "name": "Rahul Kumar"},
                    {"id": "T-2", "name": "Anitha Rao"},
                ]
            ),
            record_id_field="id",
        ),
        matching_fields=["name"],
        reconciliation_fields=["name"],
    )

    assert [reference.record_index for reference in result.source_records] == [
        0, 1, 2,
    ]
    assert [
        (match.source_index, match.target_index)
        for match in result.workflow.matches
    ] == [(0, 0), (1, 1), (2, None)]
    assert result.target_records[0].record_id == "T-1"
    assert result.target_records[1].record_id == "T-2"


def test_review_required_can_retain_a_non_null_target_index():
    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm", "customers", pd.DataFrame([{"id": "S-1", "name": "Rahul Kumar"}]),
            record_id_field="id",
        ),
        CrossSystemDataset(
            "erp", "customers", pd.DataFrame([{"id": "T-1", "name": "Rahul K"}]),
            record_id_field="id",
        ),
        matching_fields=["name"],
        reconciliation_fields=["name"],
        high_confidence_threshold=0.95,
        review_threshold=0.80,
    )

    match = result.workflow.matches[0]
    assert match.status == "review_required"
    assert match.target_index == 0
    assert result.target_records[match.target_index].record_id == "T-1"


def test_unexpected_internal_type_error_is_not_reclassified(monkeypatch):
    def fail_with_internal_error(**kwargs):
        raise TypeError("internal matcher bug")

    monkeypatch.setattr(
        cross_system,
        "run_reconciliation_workflow",
        fail_with_internal_error,
    )

    with pytest.raises(TypeError, match="internal matcher bug"):
        run_cross_system_reconciliation(
            CrossSystemDataset(
                "crm", "customers", pd.DataFrame([{"name": "Rahul"}])
            ),
            CrossSystemDataset(
                "erp", "customers", pd.DataFrame([{"name": "Rahul"}])
            ),
            matching_fields=["name"],
            reconciliation_fields=["name"],
        )


def test_expected_workflow_validation_is_translated():
    with pytest.raises(
        CrossSystemIntegrationError,
        match="At least one matching field",
    ):
        run_cross_system_reconciliation(
            CrossSystemDataset(
                "crm", "customers", pd.DataFrame([{"name": "Rahul"}])
            ),
            CrossSystemDataset(
                "erp", "customers", pd.DataFrame([{"name": "Rahul"}])
            ),
            matching_fields=[],
            reconciliation_fields=["name"],
        )


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


def test_cross_system_rejects_non_string_column_labels_consistently():
    dataset = CrossSystemDataset(
        "crm",
        "customers",
        pd.DataFrame([["Rahul"]], columns=[1]),
    )

    with pytest.raises(
        CrossSystemIntegrationError,
        match="column labels must be strings",
    ):
        run_cross_system_reconciliation(
            dataset,
            CrossSystemDataset(
                "erp",
                "customers",
                pd.DataFrame([{"name": "Rahul"}]),
            ),
            matching_fields=["name"],
            reconciliation_fields=["name"],
        )


def test_business_identifier_can_be_null_or_duplicate_without_losing_row_identity():
    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm",
            "customers",
            pd.DataFrame(
                [
                    {"id": None, "name": "Rahul"},
                    {"id": "CRM-1", "name": "Rahul"},
                    {"id": "CRM-1", "name": "Anitha"},
                ]
            ),
            record_id_field="id",
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            pd.DataFrame([{"id": "ERP-1", "name": "Rahul"}]),
            record_id_field="id",
        ),
        matching_fields=["name"],
        reconciliation_fields=["name"],
    )

    assert [reference.record_index for reference in result.source_records] == [
        0,
        1,
        2,
    ]
    assert pd.isna(result.source_records[0].record_id)
    assert [reference.record_id for reference in result.source_records[1:]] == [
        "CRM-1",
        "CRM-1",
    ]
    assert all(reference.role == "source" for reference in result.source_records)


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