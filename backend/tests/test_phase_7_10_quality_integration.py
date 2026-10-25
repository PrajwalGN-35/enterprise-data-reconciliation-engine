import pandas as pd
import pytest

import app.services.reconciliation.cross_system as cross_system
from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    CrossSystemIntegrationError,
    run_cross_system_reconciliation,
)


def _datasets():
    return (
        CrossSystemDataset(
            "crm",
            "customers",
            pd.DataFrame(
                [{"source_id": "S-1", "name": "Rahul", "amount": 10}]
            ),
            record_id_field="source_id",
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            pd.DataFrame(
                [{"target_id": "T-1", "name": "Rahul", "amount": 11}]
            ),
            record_id_field="target_id",
        ),
    )


def test_quality_assessments_are_distinct_from_matching_and_impact():
    source, target = _datasets()
    result = run_cross_system_reconciliation(
        source,
        target,
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert result.workflow.matches[0].status == "matched"
    assert result.workflow.reconciliation_results[0].status == "discrepancy"
    assert set(result.quality_assessments) == {"source", "target"}
    assert all(
        "score" in assessment and "risk" in assessment
        for assessment in result.quality_assessments.values()
    )
    assert result.workflow.impact_analysis.affected_record_count == 1


def test_quality_assessment_failure_is_explicit_and_does_not_override_matching(
    monkeypatch,
):
    source, target = _datasets()

    def fail_quality(*args, **kwargs):
        raise RuntimeError("quality engine unavailable")

    monkeypatch.setattr(
        cross_system,
        "build_reconciliation_quality_engine",
        fail_quality,
    )

    with pytest.raises(RuntimeError, match="quality engine unavailable"):
        run_cross_system_reconciliation(
            source,
            target,
            matching_fields=["name"],
            reconciliation_fields=["amount"],
        )
