import pandas as pd
from fastapi.testclient import TestClient
from uuid import uuid4

from app.core.database import SessionLocal, engine
from app.main import app
from app.models import AuditLog, CrossSystemReport
from app.services.reconciliation.cross_system import (
    CrossSystemDataset,
    run_cross_system_reconciliation,
)
from app.services.reconciliation.reporting import (
    build_cross_system_report,
    persist_cross_system_report,
)


client = TestClient(app)


def test_phase_7_12_integrated_quality_matching_reporting_and_retrieval():
    CrossSystemReport.__table__.create(bind=engine, checkfirst=True)
    result = run_cross_system_reconciliation(
        CrossSystemDataset(
            "crm",
            "customers",
            pd.DataFrame(
                [
                    {"source_id": "S-1", "name": "Rahul Kumar", "amount": 10},
                    {"source_id": "S-2", "name": "Missing", "amount": 20},
                ]
            ),
            record_id_field="source_id",
        ),
        CrossSystemDataset(
            "erp",
            "customers",
            pd.DataFrame(
                [{"target_id": "T-1", "name": "Rahul Kumer", "amount": 11}]
            ),
            record_id_field="target_id",
        ),
        matching_fields=["name"],
        reconciliation_fields=["amount"],
    )

    assert result.workflow.matches[0].status == "matched"
    assert result.workflow.matches[1].status == "no_match"
    assert set(result.quality_assessments) == {"source", "target"}

    db = SessionLocal()
    report_id = None
    try:
        report = build_cross_system_report(result, report_id=str(uuid4()))
        persisted = persist_cross_system_report(db, result)
        report_id = persisted["report_id"]
        assert report["quality_assessments"] == persisted["quality_assessments"]
        assert db.query(AuditLog).filter(
            AuditLog.entity_id == report_id,
            AuditLog.action == "cross_system_report_persisted",
        ).one()

        response = client.get(f"/reconciliation/reports/{report_id}")
        assert response.status_code == 200
        body = response.json()["report"]
        assert body["outcomes"][0]["source_reference"]["record_id"] == "S-1"
        assert body["outcomes"][1]["target_reference"] is None
        assert body["quality_assessments"]["source"]["score"] <= 100.0
    finally:
        if report_id:
            db.query(AuditLog).filter(AuditLog.entity_id == report_id).delete()
            db.query(CrossSystemReport).filter(CrossSystemReport.id == report_id).delete()
            db.commit()
        db.close()
