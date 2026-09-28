from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import AuditLog, ReconciliationRun

client = TestClient(app)


def _files(source: str, target: str):
    import io

    return {
        "source_file": (
            "source.csv",
            io.BytesIO(source.encode()),
            "text/csv",
        ),
        "target_file": (
            "target.csv",
            io.BytesIO(target.encode()),
            "text/csv",
        ),
    }


def test_failed_reconciliation_persists_failed_run_and_audit():
    source = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
    )

    target = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
    )

    with patch(
        "app.api.reconciliation.run_reconciliation_workflow",
        side_effect=RuntimeError("simulated reconciliation failure"),
    ):
        response = client.post(
            "/reconciliation/run",
            files=_files(source, target),
            data={
                "matching_fields": '["customer_id"]',
                "reconciliation_fields": '["email", "amount"]',
            },
        )

    assert response.status_code == 500
    assert "simulated reconciliation failure" in response.json()["detail"]

    db = SessionLocal()
    try:
        failed_run = (
            db.query(ReconciliationRun)
            .filter(
                ReconciliationRun.source_file_name == "source.csv",
                ReconciliationRun.target_file_name == "target.csv",
                ReconciliationRun.status == "failed",
            )
            .order_by(ReconciliationRun.created_at.desc())
            .first()
        )

        assert failed_run is not None
        assert failed_run.completed_at is not None

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == failed_run.id,
                AuditLog.action == "reconciliation_failed",
            )
            .first()
        )

        assert audit is not None
        assert "simulated reconciliation failure" in audit.details
    finally:
        db.close()


def test_completed_reconciliation_persists_run_and_audit_together():
    source = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
    )

    target = (
        "customer_id,email,amount\n"
        "C001,alice@example.com,1000\n"
    )

    response = client.post(
        "/reconciliation/run",
        files=_files(source, target),
        data={
            "matching_fields": '["customer_id"]',
            "reconciliation_fields": '["email", "amount"]',
        },
    )

    assert response.status_code == 200
    run_id = response.json()["run_id"]

    db = SessionLocal()
    try:
        run = (
            db.query(ReconciliationRun)
            .filter(ReconciliationRun.id == run_id)
            .first()
        )

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == run_id,
                AuditLog.action == "reconciliation_completed",
            )
            .first()
        )

        assert run is not None
        assert run.status == "completed"
        assert run.completed_at is not None
        assert audit is not None
    finally:
        db.close()
