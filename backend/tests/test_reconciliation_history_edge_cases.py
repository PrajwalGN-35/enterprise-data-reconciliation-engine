import io
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import AuditLog, ReconciliationRun

client = TestClient(app)


def _files(source: str, target: str):
    return {
        "source_file": (
            "edge_source.csv",
            io.BytesIO(source.encode()),
            "text/csv",
        ),
        "target_file": (
            "edge_target.csv",
            io.BytesIO(target.encode()),
            "text/csv",
        ),
    }


def test_run_history_rejects_invalid_limit():
    response = client.get("/reconciliation/runs?limit=0")

    assert response.status_code == 400
    assert "limit must be between 1 and 100" in response.json()["detail"]


def test_run_history_rejects_limit_above_maximum():
    response = client.get("/reconciliation/runs?limit=101")

    assert response.status_code == 400
    assert "limit must be between 1 and 100" in response.json()["detail"]


def test_run_history_rejects_negative_offset():
    response = client.get("/reconciliation/runs?offset=-1")

    assert response.status_code == 400
    assert "offset must be greater than or equal to 0" in response.json()["detail"]


def test_missing_run_returns_404():
    response = client.get(
        "/reconciliation/runs/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_missing_run_audit_returns_404():
    response = client.get(
        "/reconciliation/runs/00000000-0000-0000-0000-000000000000/audit"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_failed_run_appears_in_history_and_audit():
    source = (
        "customer_id,email,amount\n"
        "C901,test@example.com,1000\n"
    )

    target = (
        "customer_id,email,amount\n"
        "C901,test@example.com,1000\n"
    )

    with patch(
        "app.api.reconciliation.run_reconciliation_workflow",
        side_effect=RuntimeError("phase 4.6 simulated failure"),
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

    db = SessionLocal()
    try:
        failed_run = (
            db.query(ReconciliationRun)
            .filter(
                ReconciliationRun.source_file_name == "edge_source.csv",
                ReconciliationRun.status == "failed",
            )
            .order_by(ReconciliationRun.created_at.desc())
            .first()
        )

        assert failed_run is not None
        run_id = failed_run.id

        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_id == run_id,
                AuditLog.action == "reconciliation_failed",
            )
            .first()
        )

        assert audit is not None
    finally:
        db.close()

    history_response = client.get("/reconciliation/runs?limit=100")

    assert history_response.status_code == 200

    history = history_response.json()

    matching_runs = [
        item
        for item in history["runs"]
        if item["run_id"] == run_id
    ]

    assert len(matching_runs) == 1
    assert matching_runs[0]["status"] == "failed"

    audit_response = client.get(
        f"/reconciliation/runs/{run_id}/audit"
    )

    assert audit_response.status_code == 200

    audit_payload = audit_response.json()

    assert audit_payload["run_id"] == run_id
    assert any(
        item["action"] == "reconciliation_failed"
        for item in audit_payload["audit_logs"]
    )


def test_run_history_pagination_returns_requested_limit():
    response = client.get("/reconciliation/runs?limit=1&offset=0")

    assert response.status_code == 200

    payload = response.json()

    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert len(payload["runs"]) <= 1
    assert payload["total"] >= len(payload["runs"])
