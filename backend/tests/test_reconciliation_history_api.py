from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import AuditLog, ReconciliationRun


client = TestClient(app)


def create_test_run():
    db = SessionLocal()

    try:
        run = ReconciliationRun(
            source_file_name="history_source.csv",
            target_file_name="history_target.csv",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            source_record_count=10,
            target_record_count=10,
            matched_record_count=8,
            discrepancy_record_count=2,
            missing_target_record_count=1,
            review_required_record_count=1,
            total_discrepancy_count=2,
            reconciliation_percentage=80.0,
            exception_percentage=20.0,
            field_discrepancy_counts={"amount": 2},
        )

        db.add(run)
        db.flush()

        audit = AuditLog(
            action="reconciliation_completed",
            entity_type="reconciliation_run",
            entity_id=run.id,
            details='{"status": "completed"}',
        )

        db.add(audit)
        db.commit()
        db.refresh(run)

        return run.id

    finally:
        db.close()


def test_get_reconciliation_runs():
    run_id = create_test_run()

    response = client.get("/reconciliation/runs")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "runs" in data
    assert data["total"] >= 1

    matching_runs = [
        run for run in data["runs"]
        if run["run_id"] == run_id
    ]

    assert len(matching_runs) == 1
    assert matching_runs[0]["status"] == "completed"
    assert matching_runs[0]["source_file_name"] == "history_source.csv"


def test_get_reconciliation_run_detail():
    run_id = create_test_run()

    response = client.get(
        f"/reconciliation/runs/{run_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == run_id
    assert data["status"] == "completed"
    assert data["source_record_count"] == 10
    assert data["matched_record_count"] == 8
    assert data["discrepancy_record_count"] == 2
    assert data["field_discrepancy_counts"] == {"amount": 2}


def test_get_reconciliation_run_not_found():
    response = client.get(
        "/reconciliation/runs/does-not-exist"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_reconciliation_audit():
    run_id = create_test_run()

    response = client.get(
        f"/reconciliation/runs/{run_id}/audit"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == run_id
    assert len(data["audit_logs"]) >= 1

    audit = data["audit_logs"][0]

    assert audit["action"] == "reconciliation_completed"
    assert audit["entity_type"] == "reconciliation_run"
    assert audit["entity_id"] == run_id


def test_get_reconciliation_audit_not_found():
    response = client.get(
        "/reconciliation/runs/does-not-exist/audit"
    )

    assert response.status_code == 404


def test_get_reconciliation_runs_pagination():
    create_test_run()
    create_test_run()

    response = client.get(
        "/reconciliation/runs?limit=1&offset=0"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["runs"]) == 1


def test_get_reconciliation_runs_invalid_limit():
    response = client.get(
        "/reconciliation/runs?limit=0"
    )

    assert response.status_code == 400


def test_get_reconciliation_runs_invalid_offset():
    response = client.get(
        "/reconciliation/runs?offset=-1"
    )

    assert response.status_code == 400
