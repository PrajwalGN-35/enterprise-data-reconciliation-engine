import pandas as pd

from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    run_cross_system_reconciliation,
)


def test_large_deterministic_cross_system_run_preserves_order_and_uniqueness():
    source_rows = [
        {"source_id": f"S-{index:04d}", "name": f"Customer {index}", "amount": index}
        for index in range(100)
    ]
    target_rows = [
        {"target_id": f"T-{index:04d}", "name": f"Customer {index}", "amount": index}
        for index in reversed(range(100))
    ]

    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm", "customers", pd.DataFrame(source_rows), record_id_field="source_id"
        ),
        CrossSystemDataset(
            "erp", "customers", pd.DataFrame(target_rows), record_id_field="target_id"
        ),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert len(result.workflow.matches) == 100
    assert all(match.status == "matched" for match in result.workflow.matches)
    assert len({match.target_index for match in result.workflow.matches}) == 100
    assert [reference.record_index for reference in result.source_records] == list(range(100))
    assert [reference.record_index for reference in result.target_records] == list(range(100))
    assert result.workflow.matches[0].target_index == 99
    assert result.workflow.matches[-1].target_index == 0


def test_empty_cross_system_inputs_remain_safe_under_quality_integration():
    result = run_cross_system_reconciliation(
        CrossSystemDataset("crm", "customers", pd.DataFrame(columns=["name", "amount"])),
        CrossSystemDataset("erp", "customers", pd.DataFrame(columns=["name", "amount"])),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert result.workflow.matches == []
    assert result.quality_assessments["source"]["score"] == 100.0
    assert result.quality_assessments["target"]["score"] == 100.0
