import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.models import AuditLog, CrossSystemReport
from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    run_cross_system_reconciliation,
)
from app.services.reconciliation.reporting import (
    CrossSystemReportError,
    build_cross_system_report,
    persist_cross_system_report,
    retrieve_cross_system_report,
    serialize_report_value,
)


client = TestClient(app)


def _result(source_rows, target_rows, *, source_mapping=None, target_mapping=None, **kwargs):
    source_frame = pd.DataFrame(
        source_rows,
        columns=(
            list(source_rows[0])
            if source_rows
            else ["source_id", "name", "amount"]
        ),
    )
    target_frame = pd.DataFrame(
        target_rows,
        columns=(
            list(target_rows[0])
            if target_rows
            else ["target_id", "name", "amount"]
        ),
    )
    return run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm",
            "customers",
            source_frame,
            source_mapping,
            "source_id" if source_rows and "source_id" in source_rows[0] else None,
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            target_frame,
            target_mapping,
            "target_id" if target_rows and "target_id" in target_rows[0] else None,
        ),
        ["name"],
        ["amount"],
        **kwargs,
    )


def test_report_preserves_workflow_summary_impact_and_traceability():
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 12}],
    )

    report = build_cross_system_report(
        result,
        report_id=str(uuid4()),
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert report["schema_version"] == "7.9.1"
    assert report["source"] == {"system_name": "crm", "dataset_name": "customers"}
    assert report["summary"]["discrepancy_record_count"] == result.workflow.summary.discrepancy_record_count
    assert report["impact_analysis"] == serialize_report_value(result.workflow.impact_analysis)
    assert set(report["quality_assessments"]) == {"source", "target"}
    assert report["quality_assessments"]["source"]["dataset"] == "crm/customers"
    assert report["outcomes"][0]["source_reference"]["record_id"] == "S-1"
    assert report["outcomes"][0]["target_reference"]["record_id"] == "T-1"
    assert report["outcomes"][0]["match"]["explanation"] is not None
    assert report["outcomes"][0]["reconciliation"]["discrepancies"][0]["field"] == "amount"
    json.dumps(report, allow_nan=False)


def test_report_keeps_missing_and_review_target_references_distinct():
    missing = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [],
    )
    missing_report = build_cross_system_report(missing, report_id=str(uuid4()))
    assert missing_report["outcomes"][0]["target_reference"] is None

    review = _result(
        [{"source_id": "S-1", "name": "Rahul Kumar", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul K", "amount": 10}],
        high_confidence_threshold=0.95,
        review_threshold=0.80,
    )
    review_report = build_cross_system_report(review, report_id=str(uuid4()))
    outcome = review_report["outcomes"][0]
    assert outcome["match"]["status"] == "review_required"
    assert outcome["match"]["target_index"] == 0
    assert outcome["target_reference"]["record_id"] == "T-1"


def test_report_preserves_ambiguity_and_empty_workflow_outputs():
    ambiguous = _result(
        [{"source_id": "S-1", "name": "Rahul Kumar", "amount": 10}],
        [
            {"target_id": "T-1", "name": "Rahul Kumar", "amount": 10},
            {"target_id": "T-2", "name": "Rahul Kumar", "amount": 10},
        ],
    )
    ambiguous_report = build_cross_system_report(
        ambiguous,
        report_id=str(uuid4()),
    )
    assert ambiguous_report["outcomes"][0]["match"]["status"] == "review_required"
    assert ambiguous_report["outcomes"][0]["match"]["target_index"] is None
    assert ambiguous_report["outcomes"][0]["target_reference"] is None

    empty = _result([], [])
    empty_report = build_cross_system_report(empty, report_id=str(uuid4()))
    assert empty_report["counts"] == {
        "source_records": 0,
        "target_records": 0,
        "outcomes": 0,
    }


def test_report_strict_serializer_handles_scalars_and_rejects_unsupported_values():
    assert serialize_report_value((np.int64(2), pd.NA)) == [2, None]
    with pytest.raises(TypeError, match="Non-finite"):
        serialize_report_value(float("nan"))
    with pytest.raises(TypeError, match="Unsupported report value type"):
        serialize_report_value(object())


def test_report_rejects_inconsistent_indexes():
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 10}],
    )
    result.workflow.matches[0].target_index = 99
    with pytest.raises(CrossSystemReportError, match="target_index"):
        build_cross_system_report(result, report_id=str(uuid4()))


def test_report_rejects_mismatched_match_and_reconciliation_target_indexes():
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 10}],
    )
    result.workflow.reconciliation_results[0].target_index = None
    with pytest.raises(CrossSystemReportError, match="must agree"):
        build_cross_system_report(result, report_id=str(uuid4()))


def test_report_persistence_and_audit_are_retrievable():
    CrossSystemReport.__table__.create(bind=engine, checkfirst=True)
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 10}],
    )
    db = SessionLocal()
    report_id = None
    try:
        payload = persist_cross_system_report(db, result)
        report_id = payload["report_id"]
        saved = db.get(CrossSystemReport, report_id)
        assert saved is not None
        assert saved.schema_version == "7.9.1"
        assert retrieve_cross_system_report(db, report_id)["report_id"] == report_id
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == "cross_system_report_persisted",
                AuditLog.entity_id == report_id,
            )
            .one()
        )
        assert audit.entity_type == "cross_system_report"

        response = client.get(f"/reconciliation/reports/{report_id}")
        assert response.status_code == 200
        assert response.json()["report"]["report_id"] == report_id
    finally:
        if report_id:
            db.query(AuditLog).filter(AuditLog.entity_id == report_id).delete()
            db.query(CrossSystemReport).filter(CrossSystemReport.id == report_id).delete()
            db.commit()
        db.close()


def test_report_persistence_rolls_back_report_and_audit_on_commit_failure(
    monkeypatch,
):
    CrossSystemReport.__table__.create(bind=engine, checkfirst=True)
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 10}],
    )
    db = SessionLocal()
    before_reports = db.query(CrossSystemReport).count()
    before_audits = db.query(AuditLog).filter(
        AuditLog.action == "cross_system_report_persisted"
    ).count()

    def fail_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="commit failed"):
        persist_cross_system_report(db, result)
    db.close()

    check = SessionLocal()
    try:
        assert check.query(CrossSystemReport).count() == before_reports
        assert check.query(AuditLog).filter(
            AuditLog.action == "cross_system_report_persisted"
        ).count() == before_audits
    finally:
        check.close()


def test_report_retrieval_validates_not_found_and_malformed_ids():
    assert client.get(f"/reconciliation/reports/{uuid4()}").status_code == 404
    assert client.get("/reconciliation/reports/not-a-uuid").status_code == 400


def test_report_retrieval_rejects_corrupted_payload():
    CrossSystemReport.__table__.create(bind=engine, checkfirst=True)
    report_id = str(uuid4())
    db = SessionLocal()
    try:
        db.add(
            CrossSystemReport(
                id=report_id,
                schema_version="7.9.1",
                source_system="crm",
                source_dataset="customers",
                target_system="erp",
                target_dataset="customers",
                payload="{broken",
            )
        )
        db.commit()
    finally:
        try:
            db.query(CrossSystemReport).filter(
                CrossSystemReport.id == report_id
            ).delete()
            db.commit()
        finally:
            db.close()


@pytest.mark.parametrize(
    "mutate_payload, expected_detail",
    [
        (lambda payload, report_id: [], "JSON object"),
        (lambda payload, report_id: {**payload, "report_id": str(uuid4())}, "report ID"),
        (lambda payload, report_id: {**payload, "schema_version": "other"}, "schema version"),
        (lambda payload, report_id: {key: value for key, value in payload.items() if key != "summary"}, "summary"),
        (lambda payload, report_id: {**payload, "counts": {"source_records": 99}}, "counts"),
    ],
)
def test_report_retrieval_rejects_valid_json_with_inconsistent_integrity(
    mutate_payload,
    expected_detail,
):
    CrossSystemReport.__table__.create(bind=engine, checkfirst=True)
    result = _result(
        [{"source_id": "S-1", "name": "Rahul", "amount": 10}],
        [{"target_id": "T-1", "name": "Rahul", "amount": 10}],
    )
    report_id = str(uuid4())
    payload = build_cross_system_report(result, report_id=report_id)
    payload = mutate_payload(payload, report_id)
    db = SessionLocal()
    try:
        db.add(
            CrossSystemReport(
                id=report_id,
                schema_version="7.9.1",
                source_system="crm",
                source_dataset="customers",
                target_system="erp",
                target_dataset="customers",
                payload=json.dumps(payload),
            )
        )
        db.commit()
    finally:
        db.close()

    try:
        response = client.get(f"/reconciliation/reports/{report_id}")
        assert response.status_code == 500
        assert "invalid" in response.json()["detail"].lower()
    finally:
        db = SessionLocal()
        db.query(CrossSystemReport).filter(CrossSystemReport.id == report_id).delete()
        db.commit()
        db.close()
